"""Desk bootinfo for the platform assistant entry."""

from __future__ import annotations

import frappe

from elms.ai.api import CHAT_ROLES, _has_chat_role


def extend_bootinfo(bootinfo) -> None:
	user = getattr(getattr(frappe, "session", None), "user", None) or "Guest"
	allowed = bool(user and user != "Guest" and _has_chat_role(user))
	bootinfo["elms_assistant_allowed"] = int(allowed)
	bootinfo["elms_assistant_roles"] = sorted(CHAT_ROLES)
