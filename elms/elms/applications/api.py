"""Whitelist API for public ELMS application forms."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

import frappe

from .bitrix_leads import BitrixLeadCreateError, create_bitrix_lead
from .schemas import ApplicationSubmitPayload, parse_application_payload
from .status import get_application_status as _get_application_status
from .status import list_application_links as _list_application_links
from .status import refresh_application_status as _refresh_application_status


if not hasattr(frappe, "whitelist"):
    def _whitelist(*args: Any, **kwargs: Any):
        def decorator(function: Any) -> Any:
            return function
        if args and callable(args[0]):
            return args[0]
        return decorator
    frappe.whitelist = _whitelist

if not hasattr(frappe, "ValidationError"):
    frappe.ValidationError = ValueError


def _throw(message: str, exception: type[Exception] | None = None) -> None:
    error_type = exception or frappe.ValidationError
    throw = getattr(frappe, "throw", None)
    if callable(throw):
        throw(message, error_type)
    raise error_type(message)


def _published_courses(course_names: list[str]) -> list[dict[str, Any]]:
    names = [str(name).strip() for name in course_names if str(name).strip()]
    if not names:
        return []
    return list(
        frappe.get_all(
            "ELMS Course",
            filters={"name": ["in", names], "is_published": 1},
            fields=["name", "course_name", "course_code"],
            limit_page_length=50,
        )
        or []
    )


def _ensure_published_courses(payload: ApplicationSubmitPayload) -> None:
    names = [payload.course] if payload.application_kind == "individual" else payload.course_ids
    courses = _published_courses(names)
    if {str(row.get("name")) for row in courses} != set(names):
        _throw("Выберите опубликованный курс", frappe.ValidationError)


def _fingerprint(payload: ApplicationSubmitPayload) -> str:
    courses = payload.course or ",".join(sorted(payload.course_ids))
    source = "|".join(
        [
            payload.application_kind,
            payload.email.lower(),
            courses,
            datetime.now(timezone.utc).date().isoformat(),
        ]
    )
    return hashlib.sha256(source.encode("utf-8")).hexdigest()


def _existing_link(fingerprint: str) -> Any | None:
    exists = getattr(getattr(frappe, "db", None), "exists", None)
    if not callable(exists):
        return None
    name = exists("ELMS Application Link", {"submit_fingerprint": fingerprint})
    if not name:
        return None
    return frappe.get_doc("ELMS Application Link", name)


def _consent_at() -> str:
    now_datetime = getattr(getattr(frappe, "utils", None), "now_datetime", None)
    if callable(now_datetime):
        return str(now_datetime())
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _link_values(payload: ApplicationSubmitPayload, bitrix_id: str, fingerprint: str) -> dict[str, Any]:
    return {
        "doctype": "ELMS Application Link",
        "bitrix_id": bitrix_id,
        "bitrix_entity": "lead",
        "application_kind": payload.application_kind,
        "applicant_name": payload.fio or payload.contact_fio,
        "email": payload.email,
        "phone": payload.phone,
        "company_name": payload.company_name,
        "inn": payload.inn,
        "course": payload.course,
        "course_ids": payload.course_ids,
        "comment": payload.comment,
        "consent_at": _consent_at(),
        "submit_fingerprint": fingerprint,
    }


def _insert_link(values: dict[str, Any]) -> Any:
    link = frappe.get_doc(values)
    insert = getattr(link, "insert", None)
    if not callable(insert):
        _throw("Не удалось сохранить связь заявки с Bitrix", frappe.ValidationError)
    try:
        insert(ignore_permissions=True)
    except TypeError:
        insert()
    return link


def _result(link: Any, payload: ApplicationSubmitPayload, bitrix_id: str) -> dict[str, Any]:
    return {
        "name": str(getattr(link, "name", "")),
        "tracking_ref": str(getattr(link, "name", "")),
        "bitrix_id": bitrix_id,
        "application_kind": payload.application_kind,
    }


@frappe.whitelist(allow_guest=True, methods=["POST"])
def submit_application(payload: Any = None, **kwargs: Any) -> dict[str, Any]:
    """Validate, create a Bitrix Lead and then persist the ELMS link."""

    raw_payload = payload if payload is not None else kwargs
    try:
        application = parse_application_payload(raw_payload)
        _ensure_published_courses(application)
    except Exception as exc:
        _throw(str(exc), frappe.ValidationError)

    fingerprint = _fingerprint(application)
    existing = _existing_link(fingerprint)
    if existing is not None:
        return _result(existing, application, str(getattr(existing, "bitrix_id", "")))

    try:
        bitrix_id = create_bitrix_lead(application)
    except BitrixLeadCreateError as exc:
        _throw("Заявка не отправлена: Bitrix недоступен. Попробуйте позже.", frappe.ValidationError)
        raise AssertionError("frappe.throw must raise") from exc

    try:
        link = _insert_link(_link_values(application, bitrix_id, fingerprint))
    except Exception as exc:
        _throw("Заявка создана в Bitrix, но ELMS не сохранил tracking ref.", frappe.ValidationError)
        raise AssertionError("frappe.throw must raise") from exc
    return _result(link, application, bitrix_id)


@frappe.whitelist(allow_guest=True, methods=["GET"])
def list_published_courses() -> list[dict[str, Any]]:
    """Return only published courses needed by public form selectors."""

    return list(
        frappe.get_all(
            "ELMS Course",
            filters={"is_published": 1},
            fields=["name", "course_name", "course_code"],
            order_by="course_name asc",
            limit_page_length=100,
        )
        or []
    )


@frappe.whitelist(allow_guest=True, methods=["GET"])
def get_application_status(name: str | None = None, tracking_ref: str | None = None) -> dict[str, Any]:
    if name and not tracking_ref:
        from .status import require_operator

        require_operator()
    return _get_application_status(name=name, tracking_ref=tracking_ref)


@frappe.whitelist(allow_guest=True, methods=["POST"])
def refresh_application_status(
    name: str | None = None, tracking_ref: str | None = None
) -> dict[str, Any]:
    reference = str(tracking_ref or name or "").strip()
    if not reference:
        _throw("Укажите tracking ref заявки", frappe.ValidationError)
    return _refresh_application_status(reference, operator_only=not bool(tracking_ref))


@frappe.whitelist(methods=["GET"])
def list_application_links(application_kind: str | None = None, last_status_snapshot: str | None = None) -> list[dict[str, Any]]:
    return _list_application_links(
        {"application_kind": application_kind, "last_status_snapshot": last_status_snapshot}
    )


@frappe.whitelist(methods=["POST"])
def set_application_status(name: str, status: str) -> None:
    _throw("Статус заявки читается из Bitrix и не изменяется в ELMS", frappe.ValidationError)
