"""Behavior contracts for the B2C payment creation boundary."""

from __future__ import annotations

import json
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import frappe

from elms.admission import payment
from elms.admission.provider import FakePaymentProvider
from elms.admission.schemas import PaymentStatus


if not hasattr(frappe, "ValidationError"):
    frappe.ValidationError = ValueError
if not hasattr(frappe, "ConfigurationError"):
    frappe.ConfigurationError = RuntimeError


class FakePayment(SimpleNamespace):
    name = "PAYMENT-1"

    def __init__(self):
        super().__init__(name=self.name, flags=SimpleNamespace())
        self.saved = False
        self.inserted = False

    def insert(self, **kwargs):
        self.inserted = True
        return self

    def save(self, **kwargs):
        self.saved = True
        return self


class TestAdmissionPayment(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()
        self.payment_doc = FakePayment()

    def test_fresh_provider_instances_issue_unique_payment_ids(self):
        first_session = FakePaymentProvider(secret="test-secret").create_payment(
            15000,
            "RUB",
            {},
        )
        second_session = FakePaymentProvider(secret="test-secret").create_payment(
            15000,
            "RUB",
            {},
        )

        self.assertNotEqual(
            first_session["provider_payment_id"],
            second_session["provider_payment_id"],
        )

    def _get_value(self, doctype, name_or_filters, field=None, *args, **kwargs):
        if doctype == "ELMS Batch" and field == "course":
            return "COURSE-1"
        if doctype == "ELMS Batch" and field == "status":
            return "Active"
        if doctype == "ELMS Course" and field == "is_published":
            return 1
        return None

    def test_incomplete_profile_rejects_payment_before_provider_call(self):
        provider = MagicMock()
        with (
            patch.object(payment.frappe, "session", SimpleNamespace(user="learner@example.test"), create=True),
            patch.object(payment.frappe, "db", self.db, create=True),
            patch.object(payment, "read_admission_profile", return_value={"exists": False}),
            self.assertRaises(frappe.ValidationError),
        ):
            payment.create_payment(course="COURSE-1", batch="BATCH-1", provider=provider)

        provider.create_payment.assert_not_called()
        self.assertFalse(self.payment_doc.inserted)

    def test_complete_profile_creates_pending_payment_and_provider_session(self):
        self.db.exists.return_value = True
        self.db.get_value.side_effect = self._get_value
        provider = FakePaymentProvider(secret="test-secret")
        profile = {
            "exists": True,
            "profile": {"user": "learner@example.test"},
            "files": {
                "passport_scan": {"is_private": True},
                "snils_scan": {"is_private": True},
                "education_doc_scan": {"is_private": True},
            },
        }

        with (
            patch.object(payment.frappe, "session", SimpleNamespace(user="learner@example.test"), create=True),
            patch.object(payment.frappe, "db", self.db, create=True),
            patch.object(payment.frappe, "new_doc", return_value=self.payment_doc, create=True),
            patch.object(payment, "read_admission_profile", return_value=profile),
        ):
            result = payment.create_payment(
                course="COURSE-1",
                batch="BATCH-1",
                amount="15000",
                currency="RUB",
                provider=provider,
            )

        self.assertEqual(result["status"], PaymentStatus.PENDING.value)
        self.assertEqual(result["name"], "PAYMENT-1")
        self.assertIn("provider_session", result)
        self.assertEqual(self.payment_doc.status, PaymentStatus.PENDING.value)
        self.assertEqual(self.payment_doc.provider_payment_id, result["provider_session"]["provider_payment_id"])
        self.assertTrue(self.payment_doc.inserted)

    def test_missing_pricing_columns_use_configured_payment_amount(self):
        self.db.exists.return_value = True
        self.db.has_column.return_value = False

        def get_value_without_pricing(doctype, name_or_filters, field=None, *args, **kwargs):
            if field in {"amount", "price", "course_fee", "fee"}:
                raise AssertionError(f"unsupported pricing field queried: {doctype}.{field}")
            return self._get_value(doctype, name_or_filters, field, *args, **kwargs)

        self.db.get_value.side_effect = get_value_without_pricing
        profile = {
            "exists": True,
            "profile": {"user": "learner@example.test"},
            "files": {
                "passport_scan": {"is_private": True},
                "snils_scan": {"is_private": True},
                "education_doc_scan": {"is_private": True},
            },
        }

        with (
            patch.object(payment.frappe, "session", SimpleNamespace(user="learner@example.test"), create=True),
            patch.object(payment.frappe, "db", self.db, create=True),
            patch.object(payment.frappe, "conf", {"payment_amount": "15000"}, create=True),
            patch.object(payment.frappe, "new_doc", return_value=self.payment_doc, create=True),
            patch.object(payment, "read_admission_profile", return_value=profile),
        ):
            result = payment.create_payment(
                course="COURSE-1",
                batch="BATCH-1",
                provider=FakePaymentProvider(secret="test-secret"),
            )

        self.assertEqual(result["status"], PaymentStatus.PENDING.value)
        self.assertEqual(self.payment_doc.amount, 15000)

    def test_missing_pricing_columns_without_configuration_fail_closed(self):
        self.db.exists.return_value = True
        self.db.has_column.return_value = False
        self.db.get_value.side_effect = self._get_value
        profile = {
            "exists": True,
            "profile": {"user": "learner@example.test"},
            "files": {
                "passport_scan": {"is_private": True},
                "snils_scan": {"is_private": True},
                "education_doc_scan": {"is_private": True},
            },
        }

        with (
            patch.object(payment.frappe, "session", SimpleNamespace(user="learner@example.test"), create=True),
            patch.object(payment.frappe, "db", self.db, create=True),
            patch.object(payment.frappe, "conf", {}, create=True),
            patch.object(payment, "read_admission_profile", return_value=profile),
            self.assertRaises(frappe.ValidationError),
        ):
            payment.create_payment(
                course="COURSE-1",
                batch="BATCH-1",
                provider=FakePaymentProvider(secret="test-secret"),
            )

    def test_payment_provider_is_required_when_payments_are_enabled(self):
        self.db.exists.return_value = True
        self.db.get_value.side_effect = self._get_value
        profile = {
            "exists": True,
            "profile": {"user": "learner@example.test"},
            "files": {
                "passport_scan": {"is_private": True},
                "snils_scan": {"is_private": True},
                "education_doc_scan": {"is_private": True},
            },
        }

        with (
            patch.object(payment.frappe, "session", SimpleNamespace(user="learner@example.test"), create=True),
            patch.object(payment.frappe, "db", self.db, create=True),
            patch.object(payment, "read_admission_profile", return_value=profile),
            patch.object(payment.frappe, "conf", {"payments_enabled": 1}, create=True),
            self.assertRaises(frappe.ConfigurationError),
        ):
            payment.create_payment(course="COURSE-1", batch="BATCH-1", amount=15000, currency="RUB")


if __name__ == "__main__":
    unittest.main()
