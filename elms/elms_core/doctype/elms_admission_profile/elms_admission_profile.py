"""DocType controller for the typed learner admission profile."""

from __future__ import annotations

import frappe

try:
    from frappe.model.document import Document
except ImportError:
    class Document:  # pragma: no cover - import shim for isolated tests
        pass


MANAGER_ROLES = frozenset({"ELMS Admin", "ELMS Operations User", "System Manager"})


def has_permission(doc, ptype="read", user=None):
    """Keep the profile and its private File attachments user-scoped."""

    current = user or getattr(getattr(frappe, "session", None), "user", "Guest")
    if current == "Administrator":
        return True
    roles = set(frappe.get_roles(current) or []) if hasattr(frappe, "get_roles") else set()
    if roles.intersection(MANAGER_ROLES):
        return ptype == "read"
    return str(getattr(doc, "user", "")) == str(current) and ptype in {"read", "write", "create"}


class ELMSAdmissionProfile(Document):
    """Persist only complete, consented learner profile records."""

    def validate(self):
        if getattr(self.flags, "from_b2b_admission", False):
            if not self.user:
                frappe.throw("Профиль поступления должен ссылаться на слушателя", frappe.ValidationError)
            return
        if not self.user or not self.consent_version or not self.consent_timestamp:
            frappe.throw("Профиль должен содержать пользователя и согласие ПДн", frappe.ValidationError)
