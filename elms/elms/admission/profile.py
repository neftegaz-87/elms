"""Persistence, access control and private document handling for admission profiles."""

from __future__ import annotations

import base64
from datetime import datetime, timezone
from typing import Any

import frappe
from pydantic import ValidationError as PydanticValidationError

if not hasattr(frappe, "PermissionError"):
    frappe.PermissionError = PermissionError
if not hasattr(frappe, "ValidationError"):
    frappe.ValidationError = ValueError
try:
    from frappe.utils.file_manager import save_file
except ModuleNotFoundError:
    def save_file(filename, content, dt, dn, is_private=0, df=None):
        """Small import shim used by isolated contract tests."""

        document = frappe.get_doc(
            {
                "doctype": "File",
                "file_name": filename,
                "content": content,
                "attached_to_doctype": dt,
                "attached_to_name": dn,
                "attached_to_field": df,
                "is_private": is_private,
            }
        )
        document.insert(ignore_permissions=True)
        return document

from .schemas import LearnerProfile, parse_learner_profile


REQUIRED_SCAN_FIELDS = ("passport_scan", "snils_scan", "education_doc_scan")
MANAGER_ROLES = frozenset({"ELMS Admin", "ELMS Operations User", "System Manager"})


def _current_user() -> str:
    return str(getattr(getattr(frappe, "session", None), "user", "Guest") or "Guest")


def _roles(user: str) -> set[str]:
    if user == "Administrator":
        return {"Administrator", "System Manager"}
    get_roles = getattr(frappe, "get_roles", None)
    return set(get_roles(user) or []) if callable(get_roles) else set()


def _throw(message: str, exception: type[Exception]) -> None:
    throw = getattr(frappe, "throw", None)
    if callable(throw):
        throw(message, exception)
    raise exception(message)


def _require_authenticated() -> str:
    user = _current_user()
    if user == "Guest":
        _throw("Требуется авторизация", frappe.PermissionError)
    return user


def _require_learner() -> str:
    user = _require_authenticated()
    if "ELMS Learner" not in _roles(user):
        _throw("Профиль поступления доступен только слушателю", frappe.PermissionError)
    return user


def _is_manager(user: str) -> bool:
    return bool(_roles(user).intersection(MANAGER_ROLES))


def has_file_permission(doc: Any, ptype: str = "read", user: str | None = None) -> bool | None:
    """Restrict Admission Profile attachments while preserving File defaults."""

    if str(getattr(doc, "attached_to_doctype", "")) != "ELMS Admission Profile":
        return None

    current_user = str(user or _current_user())
    if current_user == "Guest" or ptype != "read":
        return False

    if _is_manager(current_user):
        return True
    if "ELMS Learner" not in _roles(current_user):
        return False

    profile_name = str(getattr(doc, "attached_to_name", "") or "")
    get_value = getattr(getattr(frappe, "db", None), "get_value", None)
    owner = get_value("ELMS Admission Profile", profile_name, "user") if callable(get_value) else None
    return str(owner or "") == current_user


def _now() -> str:
    now_datetime = getattr(getattr(frappe, "utils", None), "now_datetime", None)
    if callable(now_datetime):
        return str(now_datetime())
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _user_email(user: str) -> str:
    get_value = getattr(getattr(frappe, "db", None), "get_value", None)
    if callable(get_value):
        value = get_value("User", user, "email")
        if value:
            return str(value)
    return user


def _profile_name(user: str) -> str | None:
    exists = getattr(getattr(frappe, "db", None), "exists", None)
    if not callable(exists):
        return None
    value = exists("ELMS Admission Profile", {"user": user})
    return str(value) if value else None


def _decode_scan(scan: Any) -> bytes:
    value = scan.content
    encoded = value.split(",", 1)[1] if value.startswith("data:") and "," in value else value
    try:
        return base64.b64decode(encoded, validate=True)
    except (ValueError, TypeError) as exc:
        raise ValueError("Содержимое файла должно быть base64") from exc


def _attach_scan(scan: Any, fieldname: str, profile_name: str) -> Any:
    return save_file(
        scan.file_name,
        _decode_scan(scan),
        dt="ELMS Admission Profile",
        dn=profile_name,
        is_private=1,
        df=fieldname,
    )


def _previous_scan_files(profile_name: str) -> dict[str, list[str]]:
    get_all = getattr(frappe, "get_all", None)
    if not callable(get_all):
        return {}

    rows = get_all(
        "File",
        filters={
            "attached_to_doctype": "ELMS Admission Profile",
            "attached_to_name": profile_name,
            "is_private": 1,
        },
        fields=["name", "attached_to_field"],
        limit_page_length=50,
    )
    result: dict[str, list[str]] = {}
    for row in rows or []:
        fieldname = str(row.get("attached_to_field") or "")
        file_name = str(row.get("name") or "")
        if fieldname in REQUIRED_SCAN_FIELDS and file_name:
            result.setdefault(fieldname, []).append(file_name)
    return result


def _delete_replaced_files(file_names: list[str], new_file_name: str) -> None:
    delete_doc = getattr(frappe, "delete_doc", None)
    if file_names and not callable(delete_doc):
        raise RuntimeError("Frappe File deletion is unavailable while replacing an admission scan")
    for file_name in file_names:
        if file_name != new_file_name:
            delete_doc("File", file_name, force=True, ignore_permissions=True)


def _profile_values(
    model: LearnerProfile,
    user: str,
    consent_timestamp: Any = None,
) -> dict[str, Any]:
    values = model.model_dump(exclude=set(REQUIRED_SCAN_FIELDS))
    values.update(
        {
            "user": user,
            "email": _user_email(user),
            "consent_timestamp": consent_timestamp or _now(),
        }
    )
    return values


def save_admission_profile(payload: Any) -> dict[str, Any]:
    """Validate and upsert one complete profile with private attachments."""

    user = _require_learner()
    try:
        model = parse_learner_profile(payload)
    except (PydanticValidationError, ValueError) as exc:
        _throw("Анкета не прошла валидацию: заполните обязательные поля и приложите все документы", frappe.ValidationError)
        raise exc
    profile_name = _profile_name(user)
    if profile_name:
        document = frappe.get_doc("ELMS Admission Profile", profile_name)
    else:
        document = frappe.new_doc("ELMS Admission Profile")

    previous_files = _previous_scan_files(profile_name) if profile_name else {}
    previous_consent_version = getattr(document, "consent_version", None)
    previous_consent_timestamp = getattr(document, "consent_timestamp", None)
    consent_timestamp = (
        previous_consent_timestamp
        if previous_consent_version == model.consent_version
        else None
    )
    document.update(_profile_values(model, user, consent_timestamp))
    if profile_name:
        document.save(ignore_permissions=True)
    else:
        document.insert(ignore_permissions=True)

    files: dict[str, dict[str, Any]] = {}
    for fieldname in REQUIRED_SCAN_FIELDS:
        attached = _attach_scan(getattr(model, fieldname), fieldname, document.name)
        file_url = getattr(attached, "file_url", None)
        if file_url:
            setattr(document, fieldname, file_url)
        _delete_replaced_files(
            previous_files.get(fieldname, []),
            str(getattr(attached, "name", "")),
        )
        files[fieldname] = {
            "name": str(getattr(attached, "name", "")),
            "file_name": str(getattr(attached, "file_name", "")),
            "is_private": bool(getattr(attached, "is_private", 1)),
        }

    document.save(ignore_permissions=True)

    return {
        "name": str(document.name),
        "user": user,
        "complete": True,
        "consent_version": model.consent_version,
        "files": files,
    }


def _file_metadata(profile_name: str) -> dict[str, dict[str, Any]]:
    rows = frappe.get_all(
        "File",
        filters={"attached_to_doctype": "ELMS Admission Profile", "attached_to_name": profile_name},
        fields=["name", "file_name", "is_private", "attached_to_field"],
        limit_page_length=50,
    )
    return {
        str(row.get("attached_to_field")): {
            "name": str(row.get("name")),
            "file_name": str(row.get("file_name") or ""),
            "is_private": bool(row.get("is_private")),
        }
        for row in rows
        if row.get("attached_to_field") and row.get("is_private")
    }


def read_admission_profile(profile_name: str | None = None, user: str | None = None) -> dict[str, Any]:
    """Read profile data while never returning a raw file URL."""

    current = _require_authenticated()
    target_user = str(user or current)
    if target_user != current and not _is_manager(current):
        _throw("Нет доступа к профилю другого слушателя", frappe.PermissionError)
    if user and not _is_manager(current) and target_user != current:
        _throw("Нет доступа к профилю другого слушателя", frappe.PermissionError)

    name = profile_name or _profile_name(target_user)
    if not name:
        return {"exists": False, "profile": None, "files": {}}

    document = frappe.get_doc("ELMS Admission Profile", name)
    if str(getattr(document, "user", "")) != target_user and not _is_manager(current):
        _throw("Нет доступа к профилю другого слушателя", frappe.PermissionError)

    fields = (
        "name", "user", "fio_first_name", "fio_last_name", "fio_middle_name", "birth_date",
        "passport_series", "passport_number", "snils", "education_level", "profession",
        "phone", "email", "consent_version", "consent_timestamp",
    )
    values = {field: getattr(document, field, None) for field in fields}
    return {"exists": True, "profile": values, "files": _file_metadata(str(document.name))}


def safe_log_context(user: str, payload: Any) -> dict[str, Any]:
    """Return only non-sensitive diagnostics; admission PII never enters logs."""

    local, _, domain = str(user).partition("@")
    return {"user": f"{local[:2]}***@{domain}" if domain else "user***", "profile_fields_received": bool(payload)}
