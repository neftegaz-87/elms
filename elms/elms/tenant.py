"""Organization ownership and server-side LMS tenant isolation."""

from __future__ import annotations

from typing import Any

import frappe


PLATFORM_OWNER_NAME = "Демонстрационный контур НефтеГаз"
ORGANIZATION_DOCTYPE = "ELMS Organization"
MEMBER_DOCTYPE = "ELMS Organization Member"
PLATFORM_ADMIN_ROLES = {"Administrator", "System Manager", "ELMS Admin"}
COMPANY_ADMIN_ROLE = "ELMS Company Admin"

LMS_TENANT_DOCTYPES = (
	"ELMS Organization Integration",
	"ELMS Organization Role",
	"ELMS Organization Member",
	"ELMS Course",
    "ELMS Course Category",
    "ELMS Course Chapter",
    "ELMS Course Lesson",
    "ELMS Batch",
    "ELMS Subscription",
    "ELMS Enrollment",
    "ELMS Course Progress",
    "ELMS Lesson Progress",
    "ELMS User Activity",
    "ELMS Video Watch Log",
    "ELMS Program",
    "ELMS Program Course",
    "ELMS Program Enrollment",
    "ELMS Quiz",
    "ELMS Quiz Question",
    "ELMS Quiz Attempt",
)


def _roles(user: str | None = None) -> set[str]:
    current = user or getattr(frappe.session, "user", "Guest")
    if current == "Administrator":
        return set(PLATFORM_ADMIN_ROLES)
    get_roles = getattr(frappe, "get_roles", None)
    return set(get_roles(current) or []) if callable(get_roles) else set()


def is_platform_admin(user: str | None = None) -> bool:
    return bool(_roles(user).intersection(PLATFORM_ADMIN_ROLES))


def is_company_admin(user: str | None = None) -> bool:
    return COMPANY_ADMIN_ROLE in _roles(user)


def organizations_for_user(user: str | None = None) -> list[str]:
    current = user or getattr(frappe.session, "user", "Guest")
    if is_platform_admin(current):
        return []
    return [
        str(row.get("organization"))
        for row in frappe.get_all(
            MEMBER_DOCTYPE,
            filters={"user": current},
            fields=["organization"],
            limit_page_length=0,
        )
        if row.get("organization")
    ]


def ensure_platform_owner() -> str:
    owner = frappe.db.get_value(ORGANIZATION_DOCTYPE, {"is_platform_owner": 1}, "name")
    if not owner:
        owner = frappe.db.get_value(ORGANIZATION_DOCTYPE, PLATFORM_OWNER_NAME, "name")
    if not owner:
        doc = frappe.get_doc(
            {
                "doctype": ORGANIZATION_DOCTYPE,
                "organization_name": PLATFORM_OWNER_NAME,
                "inn": "0000000000",
                "status": "Active",
                "is_platform_owner": 1,
                "can_publish_own": 1,
                "can_use_owner_catalog": 1,
            }
        )
        doc.flags.ignore_permissions = True
        doc.insert()
        owner = doc.name
    frappe.db.set_value(ORGANIZATION_DOCTYPE, owner, "is_platform_owner", 1, update_modified=False)
    frappe.db.set_value(ORGANIZATION_DOCTYPE, owner, "can_publish_own", 1, update_modified=False)
    frappe.db.set_value(ORGANIZATION_DOCTYPE, owner, "can_use_owner_catalog", 1, update_modified=False)
    frappe.db.sql(
        """
        update `tabELMS Organization`
        set is_platform_owner = 0
        where name != %s and is_platform_owner = 1
        """,
        owner,
    )
    return str(owner)


def _org_filter(doctype: str, organizations: list[str]) -> str:
	escaped = ", ".join(_escape(value) for value in organizations)
	return f"{_qualified_field(doctype, 'organization')} in ({escaped})"


def _escape(value: str) -> str:
	db = getattr(frappe, "db", None)
	escape = getattr(db, "escape", None)
	if callable(escape):
		result = escape(value)
		if isinstance(result, str):
			return result
	return "'" + str(value).replace("'", "\\'") + "'"


def _qualified_name(doctype: str) -> str:
	return f"`tab{doctype}`.`name`"


def _qualified_field(doctype: str, fieldname: str) -> str:
	return f"`tab{doctype}`.`{fieldname}`"


def _clean_organization(value: Any) -> str:
    text = str(value or "").strip()
    return "" if text.casefold() in {"none", "null"} else text


def get_permission_query_conditions(user: str | None = None, doctype: str | None = None) -> str:
    """Return a fail-closed SQL scope for Frappe list and report queries."""
    current = user or getattr(frappe.session, "user", "Guest")
    doctype = doctype or ""
    if is_platform_admin(current):
        return ""
    organizations = organizations_for_user(current)
    if not organizations:
        return "1=0"
    if doctype == "User":
        values = ", ".join(_escape(value) for value in organizations)
        member_table = f"`tab{MEMBER_DOCTYPE}`"
        return (
            f"{_qualified_name('User')} in (select {member_table}.`user` "
            f"from {member_table} where {member_table}.`organization` in ({values}))"
        )
    if doctype == "ELMS Course Category":
        values = ", ".join(_escape(value) for value in organizations)
        course_table = "`tabELMS Course`"
        return (
            f"{_qualified_name(doctype)} in (select {course_table}.`category` from {course_table} "
            f"where {course_table}.`organization` in ({values}) and ifnull({course_table}.`category`, '') != '')"
        )
    if doctype in {"ELMS Course Chapter", "ELMS Course Lesson", "ELMS Quiz", "ELMS Program Course"}:
        values = ", ".join(_escape(value) for value in organizations)
        course_table = "`tabELMS Course`"
        parent = {
            "ELMS Course Chapter": "course",
            "ELMS Course Lesson": "course",
            "ELMS Quiz": "course",
            "ELMS Program Course": "course",
        }[doctype]
        return (
            f"{_qualified_field(doctype, parent)} in (select {course_table}.`name` from {course_table} "
            f"where {course_table}.`organization` in ({values}))"
        )
    return _org_filter(doctype, organizations)


def has_tenant_permission(doc: Any, user: str | None = None, permission_type: str | None = None) -> bool | None:
    doctype = str(getattr(doc, "doctype", "") or "")
    if doctype not in LMS_TENANT_DOCTYPES:
        return None
    current = user or getattr(frappe.session, "user", "Guest")
    if is_platform_admin(current):
        return None
    organization = _linked_organization(doctype, doc)
    if organization and organization in organizations_for_user(current):
        return None
    return False


def _linked_organization(doctype: str, doc: Any) -> str:
    direct = _clean_organization(getattr(doc, "organization", "") or doc.get("organization", ""))
    if direct:
        return direct
    if doctype == "ELMS Subscription":
        company = _clean_organization(getattr(doc, "company_name", "") or doc.get("company_name", ""))
        if company and frappe.db.exists(ORGANIZATION_DOCTYPE, company):
            return company
    if doctype == "ELMS Course Category":
        category = _clean_organization(getattr(doc, "name", "") or doc.get("name", ""))
        if category:
            rows = frappe.get_all("ELMS Course", filters={"category": category}, fields=["organization"], limit_page_length=2)
            organizations = {_clean_organization(row.get("organization")) for row in rows if row.get("organization")}
            if len(organizations) == 1:
                return organizations.pop()
    links = {
        "ELMS Course Chapter": ("course", "ELMS Course"),
        "ELMS Course Lesson": ("course", "ELMS Course"),
        "ELMS Quiz": ("course", "ELMS Course"),
        "ELMS Quiz Question": ("quiz", "ELMS Quiz"),
        "ELMS Quiz Attempt": ("enrollment", "ELMS Enrollment"),
        "ELMS Program Course": ("program", "ELMS Program"),
        "ELMS Enrollment": ("batch", "ELMS Batch"),
        "ELMS Course Progress": ("enrollment", "ELMS Enrollment"),
        "ELMS Lesson Progress": ("course_progress", "ELMS Course Progress"),
        "ELMS Program Enrollment": ("program", "ELMS Program"),
    }
    link = links.get(doctype)
    if link:
        value = str(getattr(doc, link[0], "") or doc.get(link[0], ""))
        if value:
            return _clean_organization(frappe.db.get_value(link[1], value, "organization"))
    if doctype in {"ELMS User Activity", "ELMS Video Watch Log"}:
        user = str(getattr(doc, "user", "") or doc.get("user", ""))
        memberships = organizations_for_user(user)
        if len(memberships) == 1:
            return memberships[0]
    return ""


def validate_lms_document(doc: Any, method: str | None = None) -> None:
    """Assign and validate the organization on every LMS document write."""
    doctype = str(getattr(doc, "doctype", ""))
    if doctype not in LMS_TENANT_DOCTYPES:
        return
    organization = _linked_organization(doctype, doc)
    current = getattr(frappe.session, "user", "Guest")
    allowed = organizations_for_user(current)
    if not organization:
        if is_company_admin(current) and len(allowed) == 1:
            organization = allowed[0]
        elif is_platform_admin(current):
            organization = ensure_platform_owner()
    if is_company_admin(current) and organization not in allowed:
        frappe.throw("Нет доступа к данным другой организации", frappe.PermissionError)
    if organization:
        if hasattr(doc, "set"):
            doc.set("organization", organization)
        else:
            doc.organization = organization
    if doctype == "ELMS Subscription" and organization:
        doc.company_name = organization


def backfill_lms_organizations() -> None:
    """Move legacy unscoped LMS rows to their owning organization."""
    ensure_platform_owner()
    for doctype in LMS_TENANT_DOCTYPES:
        for row in frappe.get_all(doctype, fields=["name"], limit_page_length=0):
            doc = frappe.get_doc(doctype, row.name)
            before = _clean_organization(doc.get("organization"))
            validate_lms_document(doc)
            after = str(doc.get("organization") or "")
            if after and after != before:
                frappe.db.set_value(doctype, doc.name, "organization", after, update_modified=False)


def clear_platform_admin_organization_scopes() -> None:
    """Remove stale organization User Permissions from globally scoped admins."""
    rows = frappe.db.sql(
        "select distinct parent as user from `tabHas Role` where role = %s",
        "ELMS Admin",
        as_dict=True,
    )
    for row in rows:
        user = str(row.get("user") or "")
        if user:
            frappe.db.delete(
                "User Permission",
                {"user": user, "allow": ORGANIZATION_DOCTYPE},
            )
