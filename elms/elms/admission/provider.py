"""Payment provider port and deterministic adapter for the admission flow."""

from __future__ import annotations

import hashlib
import hmac
import json
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping, Protocol
from uuid import uuid4

from pydantic import ValidationError as PydanticValidationError

from .schemas import PaymentEvent, PaymentSession, PaymentStatus


class PaymentProviderError(ValueError):
    """Raised when a provider payload or signature is not acceptable."""


class PaymentProviderConfigurationError(RuntimeError):
    """Raised when a payment provider is required but not configured."""


class PaymentProvider(Protocol):
    """Port implemented by a concrete payment provider adapter."""

    def create_payment(
        self,
        amount: Decimal,
        currency: str,
        meta: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        """Create a provider-side checkout session."""

    def parse_webhook(
        self,
        headers: Mapping[str, str],
        body: str | bytes,
    ) -> PaymentEvent:
        """Verify and parse a provider webhook."""


def _header(headers: Mapping[str, str], name: str) -> str:
    wanted = name.lower()
    for key, value in headers.items():
        if str(key).lower() == wanted:
            return str(value)
    return ""


def _body_text(body: str | bytes) -> str:
    if isinstance(body, bytes):
        return body.decode("utf-8")
    return str(body)


class FakePaymentProvider:
    """Small HMAC provider used by tests and local acceptance journeys."""

    def __init__(self, secret: str = "elms-test-secret") -> None:
        self.secret = secret

    def create_payment(
        self,
        amount: Decimal,
        currency: str,
        meta: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        try:
            normalized_amount = Decimal(str(amount))
        except (InvalidOperation, ValueError) as exc:
            raise PaymentProviderError("Сумма платежа должна быть числом") from exc
        if normalized_amount <= 0:
            raise PaymentProviderError("Сумма платежа должна быть больше нуля")

        provider_payment_id = f"fake-payment-{uuid4().hex}"
        session = PaymentSession(
            provider_payment_id=provider_payment_id,
            payment_url=f"https://payments.test/session/{provider_payment_id}",
            status=PaymentStatus.PENDING,
        )
        return {
            **session.model_dump(mode="json"),
            "amount": str(normalized_amount),
            "currency": str(currency).upper(),
            "metadata": dict(meta),
        }

    def parse_webhook(
        self,
        headers: Mapping[str, str],
        body: str | bytes,
    ) -> PaymentEvent:
        raw_body = _body_text(body)
        supplied = _header(headers, "X-ELMS-Signature") or _header(headers, "X-Signature")
        if supplied.startswith("sha256="):
            supplied = supplied.removeprefix("sha256=")
        expected = hmac.new(
            self.secret.encode("utf-8"),
            raw_body.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        if not supplied or not hmac.compare_digest(supplied, expected):
            raise PaymentProviderError("Недействительная подпись webhook")

        try:
            payload = json.loads(raw_body)
        except (TypeError, json.JSONDecodeError) as exc:
            raise PaymentProviderError("Webhook должен содержать JSON") from exc
        if not isinstance(payload, dict):
            raise PaymentProviderError("Webhook должен содержать JSON-объект")
        if "metadata" not in payload and isinstance(payload.get("meta"), dict):
            payload["metadata"] = payload["meta"]
        if str(payload.get("status", "")).lower() == "succeeded":
            payload["status"] = PaymentStatus.PAID.value
        try:
            return PaymentEvent.model_validate(payload)
        except PydanticValidationError as exc:
            raise PaymentProviderError("Webhook не прошёл проверку полей") from exc


def _configured_value(name: str, default: Any = None) -> Any:
    try:
        import frappe
    except ImportError:
        return default
    config = getattr(frappe, "conf", None)
    if isinstance(config, Mapping):
        return config.get(name, default)
    return getattr(config, name, default)


def get_configured_provider() -> PaymentProvider:
    """Return the configured adapter or the local fake when payments are off."""

    configured = _configured_value("payment_provider_instance")
    if configured is None:
        configured = _configured_value("payment_provider")
    if configured is not None and hasattr(configured, "create_payment") and hasattr(configured, "parse_webhook"):
        return configured

    enabled = bool(_configured_value("payments_enabled", False))
    if enabled:
        raise PaymentProviderConfigurationError("Платёжный провайдер не настроен")
    return FakePaymentProvider(secret=str(_configured_value("payment_webhook_secret", "elms-test-secret")))
