"""Whitelist endpoints for the B2C admission profile."""

from __future__ import annotations

from typing import Any

import frappe

from .payment import (
    create_payment as create_payment_for_admission,
    get_payment_status as get_payment_status_for_admission,
)
from .profile import read_admission_profile, save_admission_profile
from .webhook import handle_payment_webhook


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


@frappe.whitelist(methods=["GET", "POST"])
def get_profile(user: str | None = None) -> dict[str, Any]:
    """Return own profile, or an admin/operations read-only profile."""

    return read_admission_profile(user=user)


@frappe.whitelist(methods=["POST"])
def create_payment(
    course: str,
    batch: str,
    amount: Any = None,
    currency: str | None = None,
) -> dict[str, Any]:
    """Start the authenticated learner's payment journey."""

    return create_payment_for_admission(
        course=course,
        batch=batch,
        amount=amount,
        currency=currency,
    )


@frappe.whitelist(methods=["GET", "POST"])
def get_payment_status(payment: str) -> dict[str, Any]:
    """Return the current server-owned payment state for the learner."""

    return get_payment_status_for_admission(payment_name=payment)


@frappe.whitelist(methods=["POST"], allow_guest=True)
def payment_webhook(
    headers: dict[str, str] | None = None,
    body: str | bytes | None = None,
) -> dict[str, Any]:
    """Receive the canonical signed provider webhook without session auth."""

    request = getattr(getattr(frappe, "local", None), "request", None)
    if headers is None:
        headers = dict(getattr(request, "headers", {}) or {})
    if body is None and request is not None:
        get_data = getattr(request, "get_data", None)
        body = get_data(as_text=True) if callable(get_data) else getattr(request, "data", b"")
    if body is None:
        body = b""
    return handle_payment_webhook(headers, body)
