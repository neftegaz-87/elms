"""Server-side CSV export for the organization-scoped cabinet roster."""

from __future__ import annotations

import base64
import csv
import io
import json
import re
from datetime import datetime, timezone
from math import ceil
from typing import Any

import frappe

from elms.cabinet.roster import MAX_PAGE_SIZE, build_org_roster


MAX_EXPORT_ROWS = 5000
AUDIT_DOCTYPE = "ELMS Cabinet Export Log"
CSV_FIELDS = (
    "user",
    "full_name",
    "email",
    "user_enabled",
    "roles",
    "enrollments",
)


def _throw(message: str, exception: type[Exception]) -> None:
    throw = getattr(frappe, "throw", None)
    if callable(throw):
        throw(message, exception)
    raise exception(message)


def _current_user() -> str:
    return str(getattr(getattr(frappe, "session", None), "user", "Guest") or "Guest")


def _now_datetime() -> Any:
    utils = getattr(frappe, "utils", None)
    now_datetime = getattr(utils, "now_datetime", None)
    if callable(now_datetime):
        return now_datetime()
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _json_cell(value: Any) -> str:
    return json.dumps(value or [], ensure_ascii=False, separators=(",", ":"))


def _csv_text(rows: list[dict[str, Any]]) -> str:
    output = io.StringIO()
    output.write("\ufeff")
    writer = csv.DictWriter(output, fieldnames=CSV_FIELDS, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow(
            {
                "user": row.get("user", ""),
                "full_name": row.get("full_name", ""),
                "email": row.get("email", ""),
                "user_enabled": int(bool(row.get("user_enabled"))),
                "roles": _json_cell(row.get("roles")),
                "enrollments": _json_cell(row.get("enrollments")),
            }
        )
    return output.getvalue()


def _filename_organization(organization: str) -> str:
    safe = re.sub(r"[^0-9A-Za-z_-]+", "-", organization).strip("-")
    return safe or "organization"


def _write_audit(organization: str, row_count: int) -> None:
    values = {
        "doctype": AUDIT_DOCTYPE,
        "user": _current_user(),
        "organization": organization,
        "row_count": row_count,
        "timestamp": _now_datetime(),
    }
    get_doc = getattr(frappe, "get_doc", None)
    if not callable(get_doc):
        _throw("Не удалось записать аудит выгрузки", frappe.ValidationError)
    document = get_doc(values)
    flags = getattr(document, "flags", None)
    if flags is not None:
        flags.ignore_permissions = True
    insert = getattr(document, "insert", None)
    if not callable(insert):
        _throw("Не удалось записать аудит выгрузки", frappe.ValidationError)
    try:
        insert(ignore_permissions=True)
    except TypeError:
        insert()


def _collect_roster_rows(
    organization: str | None,
    status_filter: str | None,
) -> tuple[str, list[dict[str, Any]]]:
    first_page = build_org_roster(
        organization=organization,
        status_filter=status_filter,
        page=1,
        page_size=MAX_PAGE_SIZE,
    )
    resolved_organization = str(first_page.get("organization") or organization or "").strip()
    if not resolved_organization:
        _throw("Не удалось определить организацию для выгрузки", frappe.ValidationError)

    first_rows = list(first_page.get("rows") or [])
    try:
        total = int(first_page.get("total", len(first_rows)) or 0)
    except (TypeError, ValueError):
        _throw("Некорректное количество строк для выгрузки", frappe.ValidationError)
    if total < 0:
        _throw("Некорректное количество строк для выгрузки", frappe.ValidationError)
    if total > MAX_EXPORT_ROWS:
        _throw(
            f"Выгрузка ограничена {MAX_EXPORT_ROWS} строками; уточните организацию или фильтр",
            frappe.ValidationError,
        )
    if len(first_rows) > MAX_EXPORT_ROWS:
        _throw(
            f"Выгрузка ограничена {MAX_EXPORT_ROWS} строками; уточните организацию или фильтр",
            frappe.ValidationError,
        )

    page_size = int(first_page.get("page_size") or MAX_PAGE_SIZE)
    if page_size < 1 or page_size > MAX_PAGE_SIZE:
        page_size = MAX_PAGE_SIZE
    rows = first_rows
    for page in range(2, ceil(total / page_size) + 1):
        next_page = build_org_roster(
            organization=organization,
            status_filter=status_filter,
            page=page,
            page_size=page_size,
        )
        rows.extend(next_page.get("rows") or [])
        if len(rows) > MAX_EXPORT_ROWS:
            _throw(
                f"Выгрузка ограничена {MAX_EXPORT_ROWS} строками; уточните организацию или фильтр",
                frappe.ValidationError,
            )
    return resolved_organization, rows


def build_org_progress_export(
    organization: str | None = None,
    status_filter: str | None = None,
) -> dict[str, Any]:
    """Build and audit a UTF-8 CSV using the roster's organization ACL."""
    resolved_organization, rows = _collect_roster_rows(organization, status_filter)
    csv_text = _csv_text(rows)
    filename = f"elms-org-{_filename_organization(resolved_organization)}-{datetime.now().date():%Y%m%d}.csv"
    _write_audit(resolved_organization, len(rows))
    return {
        "filename": filename,
        "content_base64": base64.b64encode(csv_text.encode("utf-8")).decode("ascii"),
        "csv_text": csv_text,
        "charset": "UTF-8",
        "row_count": len(rows),
        "organization": resolved_organization,
    }
