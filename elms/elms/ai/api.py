"""Whitelist API for the ELMS knowledge assistant."""

from __future__ import annotations

import json
import uuid
from typing import Any

import frappe

if not hasattr(frappe, "whitelist"):
	def _whitelist(*args, **kwargs):
		def decorator(f):
			return f
		if args and callable(args[0]):
			return args[0]
		return decorator
	frappe.whitelist = _whitelist

if not hasattr(frappe, "throw"):
	def _throw(message, exc=Exception, *args, **kwargs):
		raise exc(message)
	frappe.throw = _throw

try:
	from frappe import _
except (ImportError, AttributeError):
	def _(msg: str, *args, **kwargs) -> str:
		return msg

from elms.ai import context as context_mod
from elms.ai import omniroute

CHAT_ROLES = frozenset(
	{
		"ELMS Admin",
		"ELMS Operations User",
		"ELMS Methodologist",
		"ELMS Instructor",
		"System Manager",
		"Administrator",
	}
)
MAX_HISTORY_MESSAGES = 8
MAX_HISTORY_CHARS = 8000
SYSTEM_RULES = (
	"You are the ELMS platform assistant for Desk staff. "
	"Use CONTEXT (Workspaces, Desk pages, DocTypes, whitelist APIs) plus CURRENT VIEW. "
	"When the user asks what they see on the current window/tab, explain ONLY that screen: "
	"workspace/page/route, cards, shortcuts, links, headings, labels, doctype/form fields. "
	"If CURRENT VIEW.workspace is LMS, describe Workspace LMS (learning hub). "
	"Do NOT explain ELMS Integration Settings unless CURRENT VIEW is Workspace Settings "
	"or Form/ELMS Integration Settings. "
	"If CURRENT VIEW is provided, do NOT say you cannot see the window. "
	"Do not invent API methods/DocTypes. "
	"If neither CONTEXT nor CURRENT VIEW covers the fact, set insufficient_data=true and say so briefly."
)


def _clip_text(value: Any, limit: int) -> str:
	text = str(value or "").strip()
	if len(text) <= limit:
		return text
	return text[: limit - 1] + "…"


def _clip_list(values: Any, *, item_limit: int, count: int) -> list[str]:
	if not isinstance(values, list):
		return []
	out: list[str] = []
	for item in values[:count]:
		text = _clip_text(item, item_limit)
		if text:
			out.append(text)
	return out


def _normalize_view(view: Any) -> dict[str, Any]:
	if view is None or view == "":
		return {}
	if isinstance(view, str):
		try:
			view = json.loads(view)
		except json.JSONDecodeError as exc:
			frappe.throw(_("view must be a JSON object"), frappe.ValidationError)
	if not isinstance(view, dict):
		frappe.throw(_("view must be an object"), frappe.ValidationError)
	route = view.get("route")
	route_list: list[str] = []
	if isinstance(route, list):
		route_list = [_clip_text(part, 80) for part in route[:12] if str(part or "").strip()]
	normalized = {
		"route": route_list,
		"route_str": _clip_text(view.get("route_str"), 200),
		"page": _clip_text(view.get("page"), 80),
		"workspace": _clip_text(view.get("workspace"), 80),
		"doctype": _clip_text(view.get("doctype"), 120),
		"docname": _clip_text(view.get("docname"), 140),
		"title": _clip_text(view.get("title"), 160),
		"active_tab": _clip_text(view.get("active_tab"), 80),
		"breadcrumbs": _clip_list(view.get("breadcrumbs"), item_limit=80, count=8),
		"headings": _clip_list(view.get("headings"), item_limit=120, count=16),
		"labels": _clip_list(view.get("labels"), item_limit=80, count=24),
		"pathname": _clip_text(view.get("pathname"), 200),
	}
	cleaned = {key: value for key, value in normalized.items() if value not in ("", [], None)}
	return context_mod.enrich_view(cleaned)


def _current_user() -> str:
	return getattr(getattr(frappe, "session", None), "user", None) or "Guest"


def _has_chat_role(user: str | None = None) -> bool:
	check_user = user or _current_user()
	if check_user == "Administrator":
		return True
	roles = frappe.get_roles(check_user) if hasattr(frappe, "get_roles") else []
	return bool(CHAT_ROLES.intersection(roles)) or check_user == "Administrator"


def _require_chat_role() -> None:
	user = _current_user()
	if user in (None, "", "Guest") or not _has_chat_role(user):
		frappe.throw(_("ELMS platform assistant is not available for this role"), frappe.PermissionError)


def _raise_provider_error(exc: omniroute.OmniRouteError) -> None:
	message = f"{exc} [correlation_id={exc.correlation_id}]"
	if isinstance(exc, omniroute.OmniRouteConfigError):
		frappe.throw(message, frappe.ValidationError)
	if isinstance(exc, omniroute.OmniRouteAuthError):
		frappe.throw(message, frappe.AuthenticationError if hasattr(frappe, "AuthenticationError") else frappe.ValidationError)
	frappe.throw(message, frappe.ValidationError)


def _normalize_history(history: Any) -> list[dict[str, str]]:
	if history is None or history == "":
		return []
	if isinstance(history, str):
		try:
			history = json.loads(history)
		except json.JSONDecodeError as exc:
			frappe.throw(_("history must be a JSON list of messages"), frappe.ValidationError)
	if not isinstance(history, list):
		frappe.throw(_("history must be a list"), frappe.ValidationError)
	normalized: list[dict[str, str]] = []
	total_chars = 0
	for item in history[-MAX_HISTORY_MESSAGES:]:
		if not isinstance(item, dict):
			continue
		role = str(item.get("role") or "").strip()
		content = str(item.get("content") or "").strip()
		if role not in {"user", "assistant", "system"} or not content:
			continue
		total_chars += len(content)
		if total_chars > MAX_HISTORY_CHARS:
			break
		normalized.append({"role": role, "content": content})
	return normalized


def _detect_insufficient(answer: str) -> bool:
	text = (answer or "").lower()
	markers = (
		"insufficient_data",
		"недостаточно данных",
		"недостаточно информации",
		"нет данных в context",
		"not in context",
		"cannot find",
		"не могу найти",
		"не вижу",
		"не могу определить",
		"пришлите скриншот",
		"пришлите изображение",
		"скриншот",
	)
	return any(marker in text for marker in markers)


def _is_blind_window_claim(answer: str) -> bool:
	text = (answer or "").lower()
	markers = (
		"не вижу",
		"не могу определить",
		"пришлите скриншот",
		"пришлите изображение",
		"укажите название",
		"cannot see",
		"don't see",
		"do not see",
	)
	return any(marker in text for marker in markers)


@frappe.whitelist()
def get_access() -> dict[str, Any]:
	user = _current_user()
	allowed = bool(user and user != "Guest" and _has_chat_role(user))
	return {"allowed": allowed, "roles": sorted(CHAT_ROLES)}


@frappe.whitelist()
def get_models() -> dict[str, Any]:
	_require_chat_role()
	try:
		config = omniroute.load_config()
		models = omniroute.list_models(config)
	except omniroute.OmniRouteError as exc:
		_raise_provider_error(exc)
		raise
	default_model = config.default_model
	if default_model not in models:
		models = [default_model, *models]
	return {"models": models, "default_model": default_model}


@frappe.whitelist()
def ask(
	question: str | None = None,
	model: str | None = None,
	history: Any = None,
	view: Any = None,
) -> dict[str, Any]:
	_require_chat_role()
	text = (question or "").strip()
	if not text:
		frappe.throw(_("question must not be empty"), frappe.ValidationError)

	try:
		config = omniroute.load_config()
		allowlist = omniroute.list_models(config)
	except omniroute.OmniRouteError as exc:
		_raise_provider_error(exc)
		raise

	chosen = (model or config.default_model or "").strip() or config.default_model
	if chosen not in allowlist:
		frappe.throw(
			_("Unknown model '{0}' is not in the provider allowlist").format(chosen),
			frappe.ValidationError,
		)

	try:
		pack, corpus_sources = context_mod.build_context_pack()
	except ValueError as exc:
		frappe.throw(str(exc), frappe.ValidationError)

	view_data = _normalize_view(view)
	view_block = context_mod.format_view_block(view_data)
	messages = [
		{
			"role": "system",
			"content": f"{SYSTEM_RULES}\n\n{view_block}\n\nCONTEXT:\n{pack}",
		}
	]
	messages.extend(_normalize_history(history))
	user_payload = text
	if view_data:
		user_payload = (
			f"{text}\n\n"
			f"[CLIENT CURRENT VIEW JSON]\n{json.dumps(view_data, ensure_ascii=False)}"
		)
	messages.append({"role": "user", "content": user_payload})

	local_answer = context_mod.explain_from_view(view_data)
	try:
		answer, correlation_id = omniroute.complete(messages, model=chosen, config=config)
	except omniroute.OmniRouteError as exc:
		_raise_provider_error(exc)
		raise

	if view_data and local_answer and _is_blind_window_claim(answer):
		answer = local_answer
		insufficient = False
	else:
		insufficient = _detect_insufficient(answer)
		if view_data and local_answer and insufficient:
			answer = local_answer
			insufficient = False
	source_query = answer if not insufficient else text
	if view_data.get("doctype"):
		source_query = f"{source_query} {view_data['doctype']}"
	if view_data.get("workspace"):
		source_query = f"{source_query} {view_data['workspace']}"
	if view_data.get("page"):
		source_query = f"{source_query} {view_data['page']}"
	sources = context_mod.select_sources_for_answer(
		source_query,
		corpus_sources,
		view=view_data,
	)
	return {
		"answer": answer,
		"insufficient_data": insufficient,
		"sources": sources,
		"model": chosen,
		"correlation_id": correlation_id or str(uuid.uuid4()),
		"view": view_data,
	}
