"""OpenAI-compatible HTTP client (OmniRoute and any provider via Base URL + API Key)."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import frappe

DEFAULT_TIMEOUT_SEC = 30
DEFAULT_MODEL = "cx/gpt-5.6-luna-high"
SETTINGS_DOCTYPE = "ELMS Integration Settings"


class OmniRouteError(Exception):
	def __init__(self, message: str, *, correlation_id: str | None = None, code: str = "error"):
		super().__init__(message)
		self.correlation_id = correlation_id or str(uuid.uuid4())
		self.code = code


class OmniRouteConfigError(OmniRouteError):
	def __init__(self, message: str, *, correlation_id: str | None = None):
		super().__init__(message, correlation_id=correlation_id, code="config")


class OmniRouteAuthError(OmniRouteError):
	def __init__(self, message: str, *, correlation_id: str | None = None):
		super().__init__(message, correlation_id=correlation_id, code="auth")


class OmniRouteTimeoutError(OmniRouteError):
	def __init__(self, message: str, *, correlation_id: str | None = None):
		super().__init__(message, correlation_id=correlation_id, code="timeout")


class OmniRouteTransportError(OmniRouteError):
	def __init__(self, message: str, *, correlation_id: str | None = None):
		super().__init__(message, correlation_id=correlation_id, code="transport")


class OmniRouteParseError(OmniRouteError):
	def __init__(self, message: str, *, correlation_id: str | None = None):
		super().__init__(message, correlation_id=correlation_id, code="parse")


class OmniRouteStatusError(OmniRouteError):
	def __init__(self, message: str, *, status: int | None = None, correlation_id: str | None = None):
		super().__init__(message, correlation_id=correlation_id, code="status")
		self.status = status


@dataclass(frozen=True)
class ProviderConfig:
	enabled: bool
	base_url: str
	api_key: str
	default_model: str


def _normalize_base_url(url: str) -> str:
	return (url or "").strip().rstrip("/")


def load_config() -> ProviderConfig:
	correlation_id = str(uuid.uuid4())
	try:
		doc = frappe.get_single(SETTINGS_DOCTYPE)
	except Exception as exc:
		raise OmniRouteConfigError(
			f"ELMS Integration Settings is unavailable: {exc}",
			correlation_id=correlation_id,
		) from exc

	enabled = bool(int(getattr(doc, "enabled", 0) or 0))
	base_url = _normalize_base_url(getattr(doc, "omniroute_base_url", "") or "")
	default_model = (getattr(doc, "default_model", None) or DEFAULT_MODEL).strip() or DEFAULT_MODEL
	api_key = ""
	if enabled:
		try:
			api_key = (doc.get_password("omniroute_api_key") or "").strip()
		except Exception:
			api_key = (getattr(doc, "omniroute_api_key", None) or "").strip()

	if not enabled:
		raise OmniRouteConfigError(
			"Knowledge assistant is disabled in ELMS Integration Settings",
			correlation_id=correlation_id,
		)
	if not base_url or not api_key:
		raise OmniRouteConfigError(
			"Base URL and API Key are required when the knowledge assistant is enabled",
			correlation_id=correlation_id,
		)
	return ProviderConfig(
		enabled=True,
		base_url=base_url,
		api_key=api_key,
		default_model=default_model,
	)


def _request_json(
	method: str,
	url: str,
	*,
	api_key: str,
	payload: dict[str, Any] | None = None,
	timeout: int = DEFAULT_TIMEOUT_SEC,
	correlation_id: str | None = None,
) -> Any:
	cid = correlation_id or str(uuid.uuid4())
	body = None if payload is None else json.dumps(payload).encode("utf-8")
	headers = {
		"Authorization": f"Bearer {api_key}",
		"Accept": "application/json",
		"Content-Type": "application/json",
		"X-Correlation-Id": cid,
	}
	req = Request(url, data=body, headers=headers, method=method)
	try:
		with urlopen(req, timeout=timeout) as response:
			raw = response.read().decode("utf-8")
	except TimeoutError as exc:
		raise OmniRouteTimeoutError(
			f"Provider request timed out after {timeout}s",
			correlation_id=cid,
		) from exc
	except HTTPError as exc:
		if exc.code in (401, 403):
			raise OmniRouteAuthError(
				f"Provider rejected credentials ({exc.code})",
				correlation_id=cid,
			) from exc
		raise OmniRouteStatusError(
			f"Provider returned HTTP {exc.code}",
			status=exc.code,
			correlation_id=cid,
		) from exc
	except URLError as exc:
		reason = getattr(exc, "reason", exc)
		raise OmniRouteTransportError(
			f"Provider transport error: {reason}",
			correlation_id=cid,
		) from exc

	try:
		return json.loads(raw) if raw else {}
	except json.JSONDecodeError as exc:
		raise OmniRouteParseError("Provider returned invalid JSON", correlation_id=cid) from exc


def list_models(config: ProviderConfig | None = None) -> list[str]:
	cfg = config or load_config()
	cid = str(uuid.uuid4())
	data = _request_json(
		"GET",
		f"{cfg.base_url}/models",
		api_key=cfg.api_key,
		correlation_id=cid,
	)
	items = data.get("data") if isinstance(data, dict) else None
	if not isinstance(items, list):
		raise OmniRouteParseError("Provider /models response missing data[]", correlation_id=cid)
	models: list[str] = []
	for item in items:
		if isinstance(item, dict) and item.get("id"):
			models.append(str(item["id"]))
		elif isinstance(item, str) and item.strip():
			models.append(item.strip())
	if not models:
		raise OmniRouteParseError("Provider /models returned an empty allowlist", correlation_id=cid)
	return models


def complete(
	messages: list[dict[str, str]],
	*,
	model: str,
	config: ProviderConfig | None = None,
	timeout: int = DEFAULT_TIMEOUT_SEC,
) -> tuple[str, str]:
	cfg = config or load_config()
	cid = str(uuid.uuid4())
	data = _request_json(
		"POST",
		f"{cfg.base_url}/chat/completions",
		api_key=cfg.api_key,
		payload={"model": model, "messages": messages, "temperature": 0},
		timeout=timeout,
		correlation_id=cid,
	)
	try:
		choice = data["choices"][0]
		content = choice["message"]["content"]
	except (KeyError, IndexError, TypeError) as exc:
		raise OmniRouteParseError(
			"Provider /chat/completions response missing choices[0].message.content",
			correlation_id=cid,
		) from exc
	if not isinstance(content, str) or not content.strip():
		raise OmniRouteParseError("Provider returned an empty completion", correlation_id=cid)
	return content.strip(), cid
