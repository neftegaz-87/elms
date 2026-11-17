"""Access rules for the server-owned ELMS Payment DocType."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.model.document import Document


MANAGER_ROLES = frozenset({"ELMS Admin", "ELMS Operations User", "System Manager"})


def _current_user() -> str:
	return str(getattr(getattr(frappe, "session", None), "user", "Guest") or "Guest")


def _roles(user: str) -> set[str]:
	if user == "Administrator":
		return {"Administrator", "System Manager"}
	get_roles = getattr(frappe, "get_roles", None)
	return set(get_roles(user) or []) if callable(get_roles) else set()


def has_permission(doc: Any, ptype: str = "read", user: str | None = None) -> bool:
	"""Expose payment state without allowing client-side payment mutation."""
	current_user = str(user or _current_user())
	if current_user == "Guest" or ptype != "read":
		return False
	roles = _roles(current_user)
	if roles.intersection(MANAGER_ROLES):
		return True
	return "ELMS Learner" in roles and str(getattr(doc, "user", "")) == current_user


class ELMSPayment(Document):
	pass
