"""Bitrix24 REST API transport and boundary validation models."""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Mapping

from pydantic import BaseModel, ConfigDict, field_validator, model_validator


METHOD_REGEX = re.compile(r"^[a-z][a-z0-9_]{0,63}(\.[a-z][a-z0-9_]{0,63})+$")
URL_SECRET_REGEX = re.compile(r"(https?://[^/\s]+/rest/\d+/)[^/\s]+")


def sanitize_text(text: str, secret: str | None = None) -> str:
    """Mask secret tokens in URLs and error messages."""
    if secret:
        text = text.replace(secret, "***")
    return URL_SECRET_REGEX.sub(r"\1***", text)


class BitrixRestError(Exception):
    """Raised when portal responds with error or HTTP transport fails."""

    def __init__(
        self,
        error: str,
        error_description: str | None = None,
        status_code: int | None = None,
    ) -> None:
        self.error = sanitize_text(error)
        self.error_description = (
            sanitize_text(error_description) if error_description else None
        )
        self.status_code = status_code
        msg = self.error
        if self.error_description:
            msg = f"{self.error}: {self.error_description}"
        if self.status_code:
            msg = f"[HTTP {self.status_code}] {msg}"
        super().__init__(msg)


class WebhookEndpoint(BaseModel):
    """Validated Bitrix24 incoming webhook endpoint URL."""

    url: str

    @field_validator("url", mode="before")
    @classmethod
    def validate_url(cls, v: Any) -> str:
        if not isinstance(v, str):
            raise ValueError("Webhook URL must be a string")
        v = v.strip()
        if not v:
            raise ValueError("Webhook URL must not be empty")
        parsed = urllib.parse.urlsplit(v)
        if parsed.scheme != "https":
            raise ValueError("Webhook URL scheme must be https")
        if not parsed.netloc:
            raise ValueError("Webhook URL must have a valid host")

        segments = [s for s in parsed.path.strip("/").split("/") if s]
        if len(segments) != 3:
            raise ValueError(
                f"Webhook URL path must have exactly 3 segments (/rest/<user_id>/<code>/), got {len(segments)}"
            )
        if segments[0] != "rest":
            raise ValueError(
                f"Webhook URL path first segment must be 'rest', got '{segments[0]}'"
            )
        if not segments[1].isdigit():
            raise ValueError(f"Webhook URL user ID must be digits, got '{segments[1]}'")
        if not segments[2]:
            raise ValueError("Webhook URL secret token cannot be empty")

        # Stored URL must end with trailing slash and not double-slash
        return f"https://{parsed.netloc}/rest/{segments[1]}/{segments[2]}/"

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> WebhookEndpoint:
        """Create endpoint from BITRIX_REST_WEBHOOK_URL environment variable."""
        if env is None:
            env = os.environ
        url = env.get("BITRIX_REST_WEBHOOK_URL")
        if not url or not url.strip():
            raise ValueError(
                "BITRIX_REST_WEBHOOK_URL environment variable is not set or empty"
            )
        return cls(url=url)

    @property
    def host(self) -> str:
        return urllib.parse.urlsplit(self.url).netloc

    @property
    def user_id(self) -> str:
        segments = urllib.parse.urlsplit(self.url).path.strip("/").split("/")
        return segments[1]

    @property
    def token(self) -> str:
        segments = urllib.parse.urlsplit(self.url).path.strip("/").split("/")
        return segments[2]

    @property
    def safe_url(self) -> str:
        return f"https://{self.host}/rest/{self.user_id}/***/"

    def __repr__(self) -> str:
        return f"WebhookEndpoint(url='{self.safe_url}')"

    def __str__(self) -> str:
        return self.safe_url


class CallArgs(BaseModel):
    """Validation for method name and argument payload."""

    method: str
    params: dict[str, Any] = {}

    @field_validator("method")
    @classmethod
    def validate_method_name(cls, v: str) -> str:
        if len(v) > 128:
            raise ValueError("Method name length must not exceed 128 characters")
        if v not in ("batch", "scope") and not METHOD_REGEX.match(v):
            raise ValueError(
                f"Invalid method name '{v}': must be lowercase dot-separated segments (e.g. user.current)"
            )
        return v

    @model_validator(mode="after")
    def validate_batch(self) -> CallArgs:
        if self.method == "batch":
            cmd = self.params.get("cmd")
            if isinstance(cmd, (dict, list)):
                if len(cmd) > 50:
                    raise ValueError(
                        "ERROR_BATCH_LENGTH_EXCEEDED: batch commands limit is 50"
                    )
                commands = cmd.values() if isinstance(cmd, dict) else cmd
                for item in commands:
                    if isinstance(item, str):
                        c_clean = item.strip().lower()
                        if c_clean.startswith("batch"):
                            raise ValueError(
                                "ERROR_BATCH_METHOD_NOT_ALLOWED: nested batch commands not allowed"
                            )
        return self


class RestEnvelope(BaseModel):
    """Bitrix24 REST response envelope parser."""

    model_config = ConfigDict(extra="allow")

    error: str | None = None
    error_description: str | None = None
    result: Any = None
    time: dict[str, Any] | None = None

    @model_validator(mode="after")
    def check_error(self) -> RestEnvelope:
        if self.error:
            raise BitrixRestError(
                error=self.error,
                error_description=self.error_description,
            )
        return self


class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Prevent automatic HTTP redirect following."""

    def redirect_request(
        self,
        req: urllib.request.Request,
        fp: Any,
        code: int,
        msg: str,
        headers: Any,
        newurl: str,
    ) -> None:
        return None


def post_json(
    endpoint: WebhookEndpoint,
    method: str,
    params: dict[str, Any] | None = None,
    opener: Any = None,
) -> bytes:
    """Execute Bitrix REST POST request and return raw response bytes."""
    call_args = CallArgs(method=method, params=params or {})
    req_url = f"{endpoint.url}{call_args.method}.json"
    req_data = json.dumps(call_args.params).encode("utf-8")
    req = urllib.request.Request(
        req_url,
        data=req_data,
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "Accept": "application/json",
        },
        method="POST",
    )

    if opener is None:
        opener = urllib.request.build_opener(NoRedirectHandler())

    token = endpoint.token

    try:
        with opener.open(req, timeout=30) as resp:
            status = getattr(resp, "status", None) or resp.getcode()
            body = resp.read()
    except urllib.error.HTTPError as exc:
        status = exc.code
        try:
            body = exc.read()
        except Exception:
            body = b""
        try:
            data = json.loads(body)
            if isinstance(data, dict) and data.get("error"):
                RestEnvelope.model_validate(data)
        except BitrixRestError:
            raise
        except Exception:
            pass
        raise BitrixRestError(
            error=f"http_error_{status}",
            error_description=f"HTTP status {status}",
            status_code=status,
        ) from exc
    except urllib.error.URLError as exc:
        reason = sanitize_text(str(exc.reason), token)
        raise BitrixRestError(
            error="transport_error",
            error_description=reason,
        ) from exc
    except TimeoutError as exc:
        raise BitrixRestError(
            error="timeout",
            error_description="Request timed out after 30 seconds",
        ) from exc
    except BitrixRestError:
        raise
    except Exception as exc:
        reason = sanitize_text(str(exc), token)
        raise BitrixRestError(
            error="transport_error",
            error_description=reason,
        ) from exc

    if status != 200:
        raise BitrixRestError(
            error=f"http_error_{status}",
            error_description=f"HTTP status {status}",
            status_code=status,
        )

    try:
        data = json.loads(body)
    except Exception as exc:
        raise BitrixRestError(
            error="invalid_json",
            error_description="Response body is not valid JSON",
            status_code=200,
        ) from exc

    RestEnvelope.model_validate(data)
    return body
