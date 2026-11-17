"""Server-side admission rules shared by every B2C enrollment entrypoint."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import frappe

from .schemas import PaymentStatus


def _document_value(document: Any, fieldname: str, default: Any = None) -> Any:
    if isinstance(document, Mapping):
        return document.get(fieldname, default)
    return getattr(document, fieldname, default)


def _has_available_subscription(subscription: str | None) -> bool:
    """Return whether an existing B2B subscription still has a seat."""
    if not subscription or not frappe.db.exists("ELMS Subscription", subscription):
        return False

    try:
        document = frappe.get_doc("ELMS Subscription", subscription)
    except getattr(frappe, "DoesNotExistError", Exception):
        return False

    if _document_value(document, "status") != "Active":
        return False
    try:
        seats_used = int(_document_value(document, "seats_used", 0) or 0)
        total_seats = int(_document_value(document, "total_seats", 0) or 0)
    except (TypeError, ValueError):
        return False
    return seats_used < total_seats


def require_paid_payment(
    user: str,
    batch: str,
    subscription: str | None = None,
) -> None:
    """Deny B2C enrollment unless a paid payment exists for this learner/batch.

    An active B2B subscription with an available seat is the sole bypass.  The
    caller must still perform the subscription quota mutation after this check.
    """
    if _has_available_subscription(subscription):
        return

    payment = frappe.db.get_value(
        "ELMS Payment",
        {"user": user, "batch": batch, "status": PaymentStatus.PAID.value},
        "name",
    )
    if payment:
        return

    message = "B2C enrollment requires a paid ELMS Payment"
    exception = getattr(frappe, "ValidationError", ValueError)
    if hasattr(frappe, "throw"):
        frappe.throw(message, exception)
    raise exception(message)
