"""Whitelist endpoints for the B2C admission profile."""

from __future__ import annotations

from typing import Any

import frappe

from .profile import read_admission_profile, save_admission_profile


if not hasattr(frappe, "whitelist"):
    def _whitelist(*args: Any, **kwargs: Any):
        def decorator(function: Any) -> Any:
            return function
        if args and callable(args[0]):
            return args[0]
        return decorator
    frappe.whitelist = _whitelist


@frappe.whitelist(methods=["POST"])
def save_profile(payload: Any = None, **kwargs: Any) -> dict[str, Any]:
    """Save the authenticated learner's typed profile and private scans."""

    return save_admission_profile(payload if payload is not None else kwargs)


@frappe.whitelist(methods=["GET"])
def get_profile(user: str | None = None) -> dict[str, Any]:
    """Return own profile, or an admin/operations read-only profile."""

    return read_admission_profile(user=user)
