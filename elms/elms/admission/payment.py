"""Payment creation orchestration for the B2C admission boundary."""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal, InvalidOperation
from typing import Any

import frappe

from .profile import read_admission_profile
from .provider import (
    PaymentProvider,
    PaymentProviderConfigurationError,
    PaymentProviderError,
    get_configured_provider,
)
from .schemas import PaymentSession, PaymentStatus


def _raise(name: str, message: str) -> None:
    exception = getattr(frappe, name, ValueError)
    raise exception(message)


def _current_user() -> str:
    return getattr(getattr(frappe, "session", None), "user", None) or "Guest"


def _profile_complete(profile: Any) -> bool:
    if not isinstance(profile, Mapping) or not profile.get("exists"):
        return False
    files = profile.get("files")
    if not isinstance(files, Mapping):
        return False
    required_files = ("passport_scan", "snils_scan", "education_doc_scan")
    for fieldname in required_files:
        file_info = files.get(fieldname)
        if not isinstance(file_info, Mapping) or not (
            file_info.get("is_private") or file_info.get("private")
        ):
            return False
    return True


def _ensure_batch(course: str, batch: str) -> None:
    if not frappe.db.exists("ELMS Batch", batch):
        _raise("DoesNotExistError", f"Batch {batch} does not exist")
    batch_course = frappe.db.get_value("ELMS Batch", batch, "course")
    if batch_course and course and batch_course != course:
        _raise("ValidationError", "Курс не соответствует выбранному потоку")
    batch_status = frappe.db.get_value("ELMS Batch", batch, "status")
    if batch_status and str(batch_status) not in {"Active", "Published"}:
        _raise("ValidationError", "Поток недоступен для оплаты")
    if course:
        published = frappe.db.get_value("ELMS Course", course, "is_published")
        if published is not None and not published:
            _raise("ValidationError", "Курс не опубликован")


def _configured_value(name: str, default: Any = None) -> Any:
    config = getattr(frappe, "conf", None)
    if isinstance(config, Mapping):
        return config.get(name, default)
    return getattr(config, name, default)


def _resolve_amount(course: str, batch: str, amount: Any) -> Decimal:
    candidate = amount
    if candidate in (None, ""):
        for doctype, name in (("ELMS Batch", batch), ("ELMS Course", course)):
            for fieldname in ("amount", "price", "course_fee", "fee"):
                if not frappe.db.has_column(doctype, fieldname):
                    continue
                candidate = frappe.db.get_value(doctype, name, fieldname)
                if candidate not in (None, ""):
                    break
            if candidate not in (None, ""):
                break
    if candidate in (None, ""):
        candidate = _configured_value("payment_amount")
    try:
        normalized = Decimal(str(candidate))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise getattr(frappe, "ValidationError", ValueError)(
            "Сумма оплаты должна быть настроена"
        ) from exc
    if normalized <= 0:
        _raise("ValidationError", "Сумма оплаты должна быть больше нуля")
    return normalized


def _resolve_currency(currency: Any) -> str:
    value = str(currency or _configured_value("payment_currency", "RUB")).strip().upper()
    if len(value) != 3:
        _raise("ValidationError", "Валюта оплаты должна быть ISO-кодом")
    return value


def create_payment(
    course: str,
    batch: str,
    amount: Any = None,
    currency: str | None = None,
    provider: PaymentProvider | None = None,
    user: str | None = None,
) -> dict[str, Any]:
    """Create a pending ELMS Payment after the profile gate passes."""
    learner = user or _current_user()
    if learner == "Guest":
        _raise("PermissionError", "Authentication required to start payment")
    profile = read_admission_profile(user=learner)
    if not _profile_complete(profile):
        _raise("ValidationError", "Заполните профиль, документы и согласие до оплаты")
    if not course or not batch:
        _raise("ValidationError", "Курс и поток обязательны для оплаты")
    _ensure_batch(course, batch)
    normalized_amount = _resolve_amount(course, batch, amount)
    normalized_currency = _resolve_currency(currency)

    payment_provider = provider
    if payment_provider is None:
        try:
            payment_provider = get_configured_provider()
        except PaymentProviderConfigurationError as exc:
            raise getattr(frappe, "ConfigurationError", RuntimeError)(str(exc)) from exc

    try:
        provider_payload = payment_provider.create_payment(
            normalized_amount,
            normalized_currency,
            {"user": learner, "course": course, "batch": batch},
        )
        provider_session = PaymentSession.model_validate(provider_payload)
    except PaymentProviderError as exc:
        raise getattr(frappe, "ValidationError", ValueError)(str(exc)) from exc

    payment = frappe.new_doc("ELMS Payment")
    payment.user = learner
    payment.course = course
    payment.batch = batch
    payment.amount = normalized_amount
    payment.currency = normalized_currency
    payment.status = PaymentStatus.PENDING.value
    payment.provider_payment_id = provider_session.provider_payment_id
    payment.provider_session_url = provider_session.payment_url
    if hasattr(payment, "flags"):
        payment.flags.ignore_permissions = True
    payment.insert(ignore_permissions=True)

    return {
        "name": payment.name,
        "status": payment.status,
        "provider_session": provider_session.model_dump(mode="json"),
    }


def get_payment_status(payment_name: str, user: str | None = None) -> dict[str, Any]:
    """Return an authenticated learner's payment status and learning link."""
    learner = user or _current_user()
    if learner == "Guest":
        _raise("PermissionError", "Authentication required to read payment status")
    payment = frappe.get_doc("ELMS Payment", payment_name)
    if getattr(payment, "user", None) != learner:
        _raise("PermissionError", "Payment status is available only to its learner")
    enrollment = None
    if getattr(payment, "status", None) == PaymentStatus.PAID.value:
        enrollment = frappe.db.get_value(
            "ELMS Enrollment",
            {"user": payment.user, "batch": payment.batch, "status": "Active"},
            "name",
        )
    return {
        "name": payment.name,
        "status": payment.status,
        "enrollment": enrollment,
        "learning_url": "/app/elms-learning" if enrollment else None,
    }
