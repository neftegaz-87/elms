from __future__ import annotations

from typing import Any

import frappe
from frappe.model.document import Document

from elms.tenant import is_company_admin, is_platform_admin, organizations_for_user


class ELMSAdmissionCredential(Document):
    """Protected one-time invite-token record; no learner secret is shown by list APIs."""

    def validate(self) -> None:
        if not self.login or not self.email or not self.organization:
            frappe.throw("Синтетическая identity должна иметь organization, login и email", frappe.ValidationError)


def has_permission(doc: Any, permission_type: str | None = None, user: str | None = None) -> bool:
    current = user or str(getattr(getattr(frappe, "session", None), "user", "Guest"))
    if is_platform_admin(current):
        return True
    if not is_company_admin(current) and "ELMS Operations User" not in set(frappe.get_roles(current) or []):
        return False
    return doc.organization in organizations_for_user(current)
