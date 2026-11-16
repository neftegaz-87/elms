"""Bitrix-owned application status read-back and snapshot persistence."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import frappe

from scripts.bitrix.rest_client import BitrixRestError, post_json

from elms.integrations.bitrix_config import resolve_webhook_endpoint


class ApplicationStatusError(RuntimeError):
    """Safe domain error for unavailable or invalid Bitrix status data."""


DEFAULT_STATUS_MAP = {
    "NEW": "Новая",
    "IN_PROCESS": "В работе",
    "CONVERTED": "Обработана",
    "JUNK": "Отклонена",
}
OPERATOR_ROLES = {"ELMS Admin", "ELMS Operations User", "System Manager", "Administrator"}


def _parse_status_map() -> dict[str, str]:
    get_single = getattr(frappe, "get_single", None)
    if not callable(get_single):
        return dict(DEFAULT_STATUS_MAP)
    try:
        settings = get_single("ELMS Application Settings")
    except Exception:
        return dict(DEFAULT_STATUS_MAP)
    raw = getattr(settings, "status_map", None)
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except (TypeError, ValueError):
            raw = None
    if not isinstance(raw, dict):
        return dict(DEFAULT_STATUS_MAP)
    return {str(code): str(label) for code, label in raw.items() if str(code).strip() and str(label).strip()}


def status_label(status_code: str) -> str:
    code = str(status_code or "").strip()
    return _parse_status_map().get(code, code or "Ожидает синхронизации")


def _status_code_from_response(body: bytes) -> str:
    try:
        response = json.loads(body)
    except (TypeError, ValueError) as exc:
        raise ApplicationStatusError("Bitrix returned an invalid status response") from exc
    result = response.get("result") if isinstance(response, dict) else None
    code = result.get("STATUS_ID") if isinstance(result, dict) else None
    code = str(code or "").strip()
    if not code:
        raise ApplicationStatusError("Bitrix status is missing")
    return code


def fetch_bitrix_status(bitrix_id: str) -> str:
    """Read Lead.STATUS_ID through the sole Bitrix REST transport."""

    try:
        endpoint = resolve_webhook_endpoint()
        body = post_json(endpoint, "crm.lead.get", {"id": str(bitrix_id)})
        return _status_code_from_response(body)
    except BitrixRestError as exc:
        raise ApplicationStatusError("Bitrix status is unavailable") from exc
    except (TypeError, ValueError) as exc:
        raise ApplicationStatusError("Bitrix REST configuration is invalid") from exc


def _link(name: str) -> Any:
    try:
        return frappe.get_doc("ELMS Application Link", name)
    except Exception as exc:
        error_type = getattr(frappe, "DoesNotExistError", LookupError)
        raise error_type("Application Link not found") from exc


def _snapshot_values(status_code: str) -> dict[str, str]:
    synced_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    return {
        "last_status_snapshot": status_code,
        "last_status_code": status_code,
        "display_label": status_label(status_code),
        "last_synced_at": synced_at,
    }


def persist_status_snapshot(link: Any, status_code: str) -> dict[str, Any]:
    """Persist only a read-back snapshot; never writes a local application state."""

    values = _snapshot_values(status_code)
    for field, value in values.items():
        if hasattr(link, "set"):
            link.set(field, value)
        else:
            setattr(link, field, value)
    db = getattr(frappe, "db", None)
    set_value = getattr(db, "set_value", None)
    if callable(set_value) and getattr(link, "name", None):
        set_value("ELMS Application Link", link.name, values, update_modified=False)
    return application_status(link)


def application_status(link: Any) -> dict[str, Any]:
    code = str(getattr(link, "last_status_code", None) or getattr(link, "last_status_snapshot", None) or "")
    return {
        "name": str(getattr(link, "name", "")),
        "bitrix_id": str(getattr(link, "bitrix_id", "")),
        "application_kind": str(getattr(link, "application_kind", "")),
        "status_code": code,
        "last_status_snapshot": code,
        "display_label": str(getattr(link, "display_label", None) or status_label(code)),
        "last_synced_at": str(getattr(link, "last_synced_at", "") or ""),
    }


def get_application_status(name: str | None = None, tracking_ref: str | None = None) -> dict[str, Any]:
    reference = str(name or tracking_ref or "").strip()
    if not reference:
        raise getattr(frappe, "ValidationError", ValueError)("Укажите tracking ref заявки")
    return application_status(_link(reference))


def refresh_application_status(name: str, operator_only: bool = True) -> dict[str, Any]:
    if operator_only:
        require_operator()
    link = _link(str(name).strip())
    bitrix_id = str(getattr(link, "bitrix_id", "")).strip()
    if not bitrix_id:
        raise ApplicationStatusError("Application Link has no Bitrix id")
    return persist_status_snapshot(link, fetch_bitrix_status(bitrix_id))


def _current_roles() -> set[str]:
    session = getattr(frappe, "session", None)
    user = str(getattr(session, "user", "Guest") or "Guest")
    if user == "Administrator":
        return set(OPERATOR_ROLES)
    get_roles = getattr(frappe, "get_roles", None)
    return set(get_roles(user) or []) if callable(get_roles) else set()


def require_operator() -> None:
    if not _current_roles().intersection(OPERATOR_ROLES):
        raise getattr(frappe, "PermissionError", PermissionError)("Требуется роль ELMS Admin или ELMS Operations User")


def list_application_links(filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    require_operator()
    safe_filters = {
        key: value
        for key, value in (filters or {}).items()
        if key in {"application_kind", "last_status_snapshot"} and value
    }
    return list(
        frappe.get_all(
            "ELMS Application Link",
            filters=safe_filters,
            fields=[
                "name",
                "bitrix_id",
                "application_kind",
                "applicant_name",
                "company_name",
                "last_status_snapshot",
                "display_label",
                "last_synced_at",
            ],
            order_by="creation desc",
            limit_page_length=100,
        )
        or []
    )
