"""Access rules for the ELMS Admission Profile DocType."""

from __future__ import annotations

from typing import Any

import frappe

try:
    from frappe.model.document import Document
except ImportError:
    class Document:
        """Isolated-test shim when Frappe is not installed."""


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


def has_permission(doc: Any, ptype: str = "read", user: str | None = None) -> bool:
    """Restrict profile and attached private files to the owner or read-only managers."""
    current_user = str(user or _current_user())
    if current_user == "Guest":
        return False
    roles = _roles(current_user)
    if roles.intersection(MANAGER_ROLES):
        return ptype == "read"
    return "ELMS Learner" in roles and str(getattr(doc, "user", "")) == current_user and ptype in {
        "read",
        "write",
        "create",
    }


class ELMSAdmissionProfile(Document):
    """Keep profile writes inside the authenticated learner boundary."""

    def validate(self) -> None:
        current_user = _current_user()
        if current_user == "Guest":
            _throw("Требуется авторизация", frappe.PermissionError)

        roles = _roles(current_user)
        if roles.intersection(MANAGER_ROLES):
            _throw("Профиль поступления доступен менеджерам только для чтения", frappe.PermissionError)
        if "ELMS Learner" not in roles:
            _throw("Профиль поступления доступен только слушателю", frappe.PermissionError)
        if str(getattr(self, "user", "")) != current_user:
            _throw("Слушатель может изменять только свой профиль поступления", frappe.PermissionError)
        if not getattr(self, "consent_version", None) or not getattr(self, "consent_timestamp", None):
            _throw("Версия и время согласия на обработку ПДн обязательны", frappe.ValidationError)
