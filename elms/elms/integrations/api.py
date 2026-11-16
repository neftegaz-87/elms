from __future__ import annotations

import json
from typing import Any

import frappe

from elms.access.api import require_organization_access
from elms.tenant import is_platform_admin, organizations_for_user


INTEGRATION_DOCTYPE = "ELMS Organization Integration"
INTEGRATION_TYPES = ("LLM", "Bitrix24", "Custom API")


if not hasattr(frappe, "whitelist"):
	def _whitelist(*args: Any, **kwargs: Any):
		def decorator(function: Any) -> Any:
			return function
		if args and callable(args[0]):
			return args[0]
		return decorator
	frappe.whitelist = _whitelist


if not hasattr(frappe, "PermissionError"):
	frappe.PermissionError = PermissionError
if not hasattr(frappe, "ValidationError"):
	frappe.ValidationError = ValueError


def _current_user() -> str:
	return str(getattr(getattr(frappe, "session", None), "user", "Guest") or "Guest")


def _throw(message: str, exception: type[Exception] | None = None) -> None:
	frappe.throw(message, exception or frappe.ValidationError)


def _organization(organization: str | None = None) -> str:
	value = str(organization or "").strip()
	if value:
		return require_organization_access(value)
	organizations = organizations_for_user(_current_user())
	if len(organizations) == 1:
		return require_organization_access(organizations[0])
	if not organizations and not is_platform_admin(_current_user()):
		_throw("Пользователь не состоит ни в одной организации", frappe.PermissionError)
	_throw("Укажите организацию", frappe.ValidationError)
	raise AssertionError("frappe.throw must raise")


def _secret(doc: Any, fieldname: str) -> str:
	try:
		return str(doc.get_password(fieldname) or "").strip()
	except Exception:
		return str(getattr(doc, fieldname, "") or "").strip()


def _as_row(doc: Any) -> dict[str, Any]:
	return {
		"name": str(getattr(doc, "name", "") or ""),
		"organization": str(getattr(doc, "organization", "") or ""),
		"integration_type": str(getattr(doc, "integration_type", "") or ""),
		"enabled": bool(getattr(doc, "enabled", 0)),
		"base_url": str(getattr(doc, "base_url", "") or ""),
		"default_model": str(getattr(doc, "default_model", "") or ""),
		"config_json": str(getattr(doc, "config_json", "") or ""),
		"api_key_configured": bool(_secret(doc, "api_key")),
		"webhook_configured": bool(_secret(doc, "webhook_url")),
	}


def _validate_type(integration_type: str) -> str:
	value = str(integration_type or "").strip()
	if value not in INTEGRATION_TYPES:
		_throw("Недопустимый тип интеграции", frappe.ValidationError)
	return value


def _clean_config(value: Any) -> str:
	if value in (None, ""):
		return ""
	if isinstance(value, dict):
		return json.dumps(value, ensure_ascii=False, sort_keys=True)
	text = str(value).strip()
	if len(text) > 10000:
		_throw("Дополнительная конфигурация слишком длинная", frappe.ValidationError)
	if text:
		try:
			json.loads(text)
		except json.JSONDecodeError as exc:
			_throw(f"Дополнительная конфигурация должна быть JSON: {exc}", frappe.ValidationError)
	return text


def _find(organization: str, integration_type: str) -> Any | None:
	name = frappe.db.exists(
		INTEGRATION_DOCTYPE,
		{"organization": organization, "integration_type": integration_type},
	)
	return frappe.get_doc(INTEGRATION_DOCTYPE, name) if name else None


@frappe.whitelist()
def get_organization_integrations(organization: str | None = None) -> dict[str, Any]:
	platform_admin = is_platform_admin(_current_user())
	selected = str(organization or "").strip()
	if selected:
		selected = require_organization_access(selected)
	elif not platform_admin:
		selected = _organization()
	organization_rows = frappe.get_all("ELMS Organization", fields=["name"], order_by="name asc", limit_page_length=0) if platform_admin else [{"name": selected}]
	if not selected:
		return {
			"organization": "",
			"organizations": [str(row.get("name") or "") for row in organization_rows],
			"platform_admin": True,
			"integration_types": list(INTEGRATION_TYPES),
			"integrations": [],
		}
	rows = frappe.get_all(INTEGRATION_DOCTYPE, filters={"organization": selected}, fields=["name"], order_by="integration_type asc", limit_page_length=100)
	docs = [frappe.get_doc(INTEGRATION_DOCTYPE, row.get("name")) for row in rows]
	return {
		"organization": selected,
		"organizations": [str(row.get("name") or "") for row in organization_rows],
		"platform_admin": platform_admin,
		"integration_types": list(INTEGRATION_TYPES),
		"integrations": [_as_row(doc) for doc in docs],
	}


@frappe.whitelist()
def save_organization_integration(
	organization: str,
	integration_type: str,
	enabled: Any = 0,
	base_url: str | None = None,
	default_model: str | None = None,
	api_key: str | None = None,
	webhook_url: str | None = None,
	config_json: Any = None,
) -> dict[str, Any]:
	selected = _organization(organization)
	type_name = _validate_type(integration_type)
	doc = _find(selected, type_name)
	if doc is None:
		doc = frappe.get_doc({"doctype": INTEGRATION_DOCTYPE, "organization": selected, "integration_type": type_name})
	doc.organization = selected
	doc.integration_type = type_name
	doc.enabled = int(bool(enabled))
	doc.base_url = str(base_url or "").strip()
	doc.default_model = str(default_model or "").strip()
	doc.config_json = _clean_config(config_json)
	if str(api_key or "").strip():
		doc.api_key = str(api_key).strip()
	if str(webhook_url or "").strip():
		doc.webhook_url = str(webhook_url).strip()
	doc.flags.ignore_permissions = True
	if getattr(doc, "is_new", lambda: False)():
		doc.insert(ignore_permissions=True)
	else:
		doc.save(ignore_permissions=True)
	return _as_row(doc)


@frappe.whitelist()
def delete_organization_integration(organization: str, integration_type: str) -> dict[str, str]:
	selected = _organization(organization)
	type_name = _validate_type(integration_type)
	doc = _find(selected, type_name)
	if doc is None:
		_throw("Интеграция не найдена", frappe.DoesNotExistError)
	doc.delete(ignore_permissions=True)
	return {"organization": selected, "integration_type": type_name, "status": "deleted"}
