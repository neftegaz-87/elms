"""Organization-scoped roster read model for the company cabinet."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import frappe

from elms.access.api import (
    MEMBER_DOCTYPE,
    ORGANIZATION_DOCTYPE,
    require_organization_access,
)


ENROLLMENT_DOCTYPE = "ELMS Enrollment"
PROGRESS_DOCTYPE = "ELMS Course Progress"
USER_DOCTYPE = "User"
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 500
ENROLLMENT_STATUSES = frozenset({"Active", "Completed", "Suspended", "Cancelled"})


@dataclass(frozen=True)
class EnrollmentDTO:
    enrollment: str
    course: str
    course_name: str
    status: str
    progress_pct: float

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class OrgRosterDTO:
    user: str
    full_name: str
    email: str
    user_enabled: bool
    roles: tuple[str, ...]
    enrollments: tuple[EnrollmentDTO, ...]

    def as_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["roles"] = list(self.roles)
        value["enrollments"] = [item.as_dict() for item in self.enrollments]
        return value


def _throw(message: str, exception: type[Exception]) -> None:
    frappe.throw(message, exception)


def _current_user() -> str:
    return str(getattr(getattr(frappe, "session", None), "user", "Guest") or "Guest")


def _organization_exists(organization: str) -> bool:
    db = getattr(frappe, "db", None)
    exists = getattr(db, "exists", None)
    if not callable(exists):
        return False
    return bool(exists(ORGANIZATION_DOCTYPE, organization) or exists(ORGANIZATION_DOCTYPE, {"name": organization}))


def _as_positive_int(value: Any, field: str, default: int) -> int:
    if value in (None, ""):
        return default
    try:
        result = int(value)
    except (TypeError, ValueError):
        _throw(f"Поле {field} должно быть целым числом", frappe.ValidationError)
    if result < 1:
        _throw(f"Поле {field} должно быть больше нуля", frappe.ValidationError)
    return result


def _page_size(value: Any) -> int:
    result = _as_positive_int(value, "page_size", DEFAULT_PAGE_SIZE)
    if result > MAX_PAGE_SIZE:
        _throw(f"page_size не может быть больше {MAX_PAGE_SIZE}", frappe.ValidationError)
    return result


def _resolve_organization(organization: str | None, user: str) -> str:
    requested = str(organization or "").strip()
    if requested:
        if not _organization_exists(requested):
            _throw("Организация не найдена", frappe.DoesNotExistError)
        return require_organization_access(requested, user)

    memberships = frappe.get_all(
        MEMBER_DOCTYPE,
        filters={"user": user},
        fields=["organization", "is_primary"],
        order_by="is_primary desc, modified asc",
        limit_page_length=MAX_PAGE_SIZE,
    )
    if not memberships:
        _throw("У пользователя нет организации", frappe.PermissionError)
    primary = next((row for row in memberships if row.get("is_primary")), memberships[0])
    resolved = str(primary.get("organization") or "").strip()
    if not resolved:
        _throw("У пользователя нет организации", frappe.PermissionError)
    return require_organization_access(resolved, user)


def _member_count(organization: str) -> int:
    db = getattr(frappe, "db", None)
    count = getattr(db, "count", None)
    if not callable(count):
        _throw("Не удалось определить количество участников", frappe.ValidationError)
    return int(count(MEMBER_DOCTYPE, filters={"organization": organization}) or 0)


def _record_organization_view(actor: str, organization: str) -> None:
    """Persist the read event in the existing ELMS User Activity journal."""
    get_doc = getattr(frappe, "get_doc", None)
    if not callable(get_doc):
        return
    now_datetime = getattr(getattr(frappe, "utils", None), "now_datetime", None)
    values = {
        "doctype": "ELMS User Activity",
        "user": actor,
        "organization": organization,
        "activity_type": "Organization View",
        "timestamp": now_datetime() if callable(now_datetime) else None,
        "reference_doctype": ORGANIZATION_DOCTYPE,
        "reference_name": organization,
        "ip_address": getattr(getattr(frappe, "local", None), "request_ip", "127.0.0.1"),
    }
    activity = get_doc(values)
    for field, value in values.items():
        if field != "doctype":
            setattr(activity, field, value)
    insert = getattr(activity, "insert", None)
    if not callable(insert):
        _throw("Не удалось записать аудит просмотра организации", frappe.ValidationError)
    try:
        insert(ignore_permissions=True)
    except TypeError:
        insert()


def _user_map(user_names: list[str]) -> dict[str, dict[str, Any]]:
    if not user_names:
        return {}
    rows = frappe.get_all(
        USER_DOCTYPE,
        filters={"name": ["in", user_names]},
        fields=["name", "email", "first_name", "last_name", "full_name", "enabled"],
        limit_page_length=len(user_names),
    )
    return {str(row.get("name")): row for row in rows}


def _enrollment_map(user_names: list[str], status_filter: str | None) -> dict[str, list[dict[str, Any]]]:
    if not user_names:
        return {}
    filters: dict[str, Any] = {"user": ["in", user_names]}
    if status_filter:
        filters["status"] = status_filter
    rows = frappe.get_all(
        ENROLLMENT_DOCTYPE,
        filters=filters,
        fields=["name", "user", "course", "course_name", "status"],
        order_by="user asc, modified desc",
        limit_page_length=MAX_PAGE_SIZE * len(user_names),
    )
    result: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        result.setdefault(str(row.get("user")), []).append(row)
    return result


def _progress_map(enrollment_names: list[str]) -> dict[str, float]:
    if not enrollment_names:
        return {}
    rows = frappe.get_all(
        PROGRESS_DOCTYPE,
        filters={"enrollment": ["in", enrollment_names]},
        fields=["enrollment", "progress_percentage"],
        limit_page_length=MAX_PAGE_SIZE * len(enrollment_names),
    )
    return {
        str(row.get("enrollment")): float(row.get("progress_percentage") or 0)
        for row in rows
    }


def build_org_roster(
    organization: str | None = None,
    status_filter: str | None = None,
    page: int | str | None = 1,
    page_size: int | str | None = DEFAULT_PAGE_SIZE,
    user: str | None = None,
) -> dict[str, Any]:
    current_user = user or _current_user()
    size = _page_size(page_size)
    page_number = _as_positive_int(page, "page", 1)
    normalized_status = str(status_filter or "").strip()
    if normalized_status and normalized_status not in ENROLLMENT_STATUSES:
        _throw("Недопустимый статус зачисления", frappe.ValidationError)
    resolved_organization = _resolve_organization(organization, current_user)

    members = frappe.get_all(
        MEMBER_DOCTYPE,
        filters={"organization": resolved_organization},
        fields=["user", "role_profile"],
        order_by="user asc",
        limit_start=(page_number - 1) * size,
        limit_page_length=size,
    )
    user_names = [str(row.get("user")) for row in members if row.get("user")]
    users = _user_map(user_names)
    enrollments_by_user = _enrollment_map(user_names, normalized_status or None)
    enrollment_names = [
        str(enrollment.get("name"))
        for enrollments in enrollments_by_user.values()
        for enrollment in enrollments
        if enrollment.get("name")
    ]
    progress_by_enrollment = _progress_map(enrollment_names)

    roster_rows: list[dict[str, Any]] = []
    for member in members:
        user_name = str(member.get("user") or "")
        user_row = users.get(user_name, {})
        profile = str(member.get("role_profile") or "")
        roles = [profile] if profile else []
        if profile == "ELMS Learner Profile":
            roles.append("ELMS Learner")
        elif profile == "ELMS Company Admin Profile":
            roles.append("ELMS Company Admin")
        enrollment_dtos = tuple(
            EnrollmentDTO(
                enrollment=str(enrollment.get("name") or ""),
                course=str(enrollment.get("course") or ""),
                course_name=str(enrollment.get("course_name") or ""),
                status=str(enrollment.get("status") or ""),
                progress_pct=progress_by_enrollment.get(str(enrollment.get("name") or ""), 0.0),
            )
            for enrollment in enrollments_by_user.get(user_name, [])
        )
        roster_rows.append(
            OrgRosterDTO(
                user=user_name,
                full_name=str(user_row.get("full_name") or " ".join(filter(None, [user_row.get("first_name"), user_row.get("last_name")])) or user_name),
                email=str(user_row.get("email") or user_name),
                user_enabled=bool(user_row.get("enabled", 0)),
                roles=tuple(roles),
                enrollments=enrollment_dtos,
            ).as_dict()
        )

    result = {
        "organization": resolved_organization,
        "total": _member_count(resolved_organization),
        "page": page_number,
        "page_size": size,
        "rows": roster_rows,
        "empty": not roster_rows,
    }
    _record_organization_view(current_user, resolved_organization)
    return result
