"""Signed payment webhook handling and one-time B2C enrollment."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import frappe

from elms.lms import api as lms_api

from .provider import (
    PaymentProvider,
    PaymentProviderConfigurationError,
    PaymentProviderError,
    get_configured_provider,
)
from .schemas import PaymentStatus


def _raise(name: str, message: str) -> None:
    exception = getattr(frappe, name, ValueError)
    raise exception(message)


def _payment_name(provider_payment_id: str) -> str | None:
    return frappe.db.get_value(
        "ELMS Payment",
        {"provider_payment_id": provider_payment_id},
        "name",
    )


def handle_payment_webhook(
    headers: Mapping[str, str],
    body: str | bytes,
    provider: PaymentProvider | None = None,
) -> dict[str, Any]:
    """Verify a provider event and apply its paid/failed transition once."""
    payment_provider = provider
    if payment_provider is None:
        try:
            payment_provider = get_configured_provider()
        except PaymentProviderConfigurationError as exc:
            raise getattr(frappe, "ConfigurationError", RuntimeError)(str(exc)) from exc

    try:
        event = payment_provider.parse_webhook(headers, body)
    except PaymentProviderError as exc:
        raise getattr(frappe, "ValidationError", ValueError)(str(exc)) from exc

    payment_name = _payment_name(event.provider_payment_id)
    if not payment_name:
        _raise("DoesNotExistError", "Платёж для webhook не найден")
    payment = frappe.get_doc("ELMS Payment", payment_name)
    if getattr(payment, "last_event_id", None) == event.event_id:
        return {
            "ack": True,
            "duplicate": True,
            "event_id": event.event_id,
            "payment": payment.name,
            "status": payment.status,
            "enrollment": None,
        }

    payment.status = event.status.value
    payment.last_event_id = event.event_id
    payment.save(ignore_permissions=True)
    enrollment = None
    if event.status == PaymentStatus.PAID:
        enrollment = frappe.db.get_value(
            "ELMS Enrollment",
            {"user": payment.user, "batch": payment.batch, "status": "Active"},
            "name",
        )
        if not enrollment:
            result = lms_api.enroll_learner(
                user=payment.user,
                batch=payment.batch,
                subscription=getattr(payment, "subscription", None),
                payment_id=payment.name,
            )
            enrollment = result.get("enrollment") if isinstance(result, Mapping) else result
    return {
        "ack": True,
        "duplicate": False,
        "event_id": event.event_id,
        "payment": payment.name,
        "status": payment.status,
        "enrollment": enrollment,
    }
