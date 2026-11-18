from __future__ import annotations

from typing import Any

import frappe
from frappe.model.document import Document

from elms.tenant import is_company_admin, is_platform_admin, organizations_for_user


class ELMSAdmissionImport(Document):
    """Parent document for one organization-scoped workbook revision."""

    def validate(self) -> None:
        user = str(getattr(getattr(frappe, "session", None), "user", "Guest"))
        if is_platform_admin(user):
            return
        if not is_company_admin(user):
            frappe.throw("Импорт доступен только администратору организации", frappe.PermissionError)
        allowed = organizations_for_user(user)
        if not self.organization and len(allowed) == 1:
            self.organization = allowed[0]
        if self.organization not in allowed:
            frappe.throw("Нет доступа к данным другой организации", frappe.PermissionError)

    def on_update(self) -> None:
        if str(self.status or "") not in {"draft", "parsed", "failed"}:
            frappe.throw("Недопустимый статус импорта", frappe.ValidationError)


def has_permission(doc: Any, permission_type: str | None = None, user: str | None = None) -> bool:
    current = user or str(getattr(getattr(frappe, "session", None), "user", "Guest"))
    if is_platform_admin(current):
        return True
    return bool(is_company_admin(current) and doc.organization in organizations_for_user(current))
