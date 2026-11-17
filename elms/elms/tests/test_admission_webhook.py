"""Signed payment webhook and idempotent enrollment contracts."""

from __future__ import annotations

import hashlib
import hmac
import json
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import frappe

from elms.admission import webhook
from elms.admission.provider import FakePaymentProvider
from elms.admission.schemas import PaymentStatus


if not hasattr(frappe, "ValidationError"):
    frappe.ValidationError = ValueError
if not hasattr(frappe, "DoesNotExistError"):
    frappe.DoesNotExistError = LookupError


class FakePayment(SimpleNamespace):
    def __init__(self, status=PaymentStatus.PENDING.value, last_event_id=None):
        super().__init__(
            name="PAYMENT-1",
            user="learner@example.test",
            batch="BATCH-1",
            course="COURSE-1",
            subscription=None,
            status=status,
            provider_payment_id="provider-1",
            last_event_id=last_event_id,
            flags=SimpleNamespace(),
        )
        self.saved = False

    def save(self, **kwargs):
        self.saved = True
        return self


def signed_headers(body: str, secret: str = "test-secret"):
    signature = hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()
    return {"X-ELMS-Signature": f"sha256={signature}"}


class TestAdmissionWebhook(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()
        self.payment_doc = FakePayment()
        self.provider = FakePaymentProvider(secret="test-secret")

        def get_value(doctype, filters_or_name, field=None, *args, **kwargs):
            if doctype == "ELMS Payment":
                return "PAYMENT-1"
            if doctype == "ELMS Enrollment":
                return None
            return None

        self.db.get_value.side_effect = get_value

    def _body(self, status):
        return json.dumps(
            {
                "event_id": "EVENT-1",
                "payment_id": "provider-1",
                "status": status,
            }
        )

    def test_signed_paid_webhook_enrolls_once_with_payment_reference(self):
        body = self._body("paid")
        with (
            patch.object(webhook.frappe, "db", self.db, create=True),
            patch.object(webhook.frappe, "get_doc", return_value=self.payment_doc, create=True),
            patch.object(webhook.lms_api, "enroll_learner", return_value={"enrollment": "ENROLLMENT-1"}) as enroll,
        ):
            result = webhook.handle_payment_webhook(signed_headers(body), body, provider=self.provider)

        self.assertEqual(result["status"], PaymentStatus.PAID.value)
        self.assertEqual(result["enrollment"], "ENROLLMENT-1")
        self.assertEqual(self.payment_doc.status, PaymentStatus.PAID.value)
        self.assertEqual(self.payment_doc.last_event_id, "EVENT-1")
        enroll.assert_called_once_with(
            user="learner@example.test",
            batch="BATCH-1",
            subscription=None,
            payment_id="PAYMENT-1",
        )

    def test_signed_paid_webhook_persists_paid_state_before_enrollment(self):
        body = self._body("paid")
        observed_payment_state = []

        def enroll(**kwargs):
            observed_payment_state.append(
                (self.payment_doc.status, self.payment_doc.saved)
            )
            return {"enrollment": "ENROLLMENT-1"}

        with (
            patch.object(webhook.frappe, "db", self.db, create=True),
            patch.object(webhook.frappe, "get_doc", return_value=self.payment_doc, create=True),
            patch.object(webhook.lms_api, "enroll_learner", side_effect=enroll),
        ):
            result = webhook.handle_payment_webhook(
                signed_headers(body), body, provider=self.provider
            )

        self.assertEqual(result["status"], PaymentStatus.PAID.value)
        self.assertEqual(
            observed_payment_state,
            [(PaymentStatus.PAID.value, True)],
        )

    def test_duplicate_event_id_does_not_enroll_again(self):
        body = self._body("paid")
        self.payment_doc.last_event_id = "EVENT-1"
        with (
            patch.object(webhook.frappe, "db", self.db, create=True),
            patch.object(webhook.frappe, "get_doc", return_value=self.payment_doc, create=True),
            patch.object(webhook.lms_api, "enroll_learner") as enroll,
        ):
            result = webhook.handle_payment_webhook(signed_headers(body), body, provider=self.provider)

        self.assertTrue(result["duplicate"])
        enroll.assert_not_called()

    def test_failed_webhook_updates_payment_without_active_enrollment(self):
        body = self._body("failed")
        with (
            patch.object(webhook.frappe, "db", self.db, create=True),
            patch.object(webhook.frappe, "get_doc", return_value=self.payment_doc, create=True),
            patch.object(webhook.lms_api, "enroll_learner") as enroll,
        ):
            result = webhook.handle_payment_webhook(signed_headers(body), body, provider=self.provider)

        self.assertEqual(result["status"], PaymentStatus.FAILED.value)
        self.assertIsNone(result["enrollment"])
        self.assertEqual(self.payment_doc.status, PaymentStatus.FAILED.value)
        enroll.assert_not_called()

    def test_unsigned_webhook_is_rejected_before_payment_mutation(self):
        body = self._body("paid")
        with (
            patch.object(webhook.frappe, "db", self.db, create=True),
            patch.object(webhook.frappe, "get_doc", return_value=self.payment_doc, create=True),
            self.assertRaises(frappe.ValidationError),
        ):
            webhook.handle_payment_webhook({}, body, provider=self.provider)

        self.assertEqual(self.payment_doc.status, PaymentStatus.PENDING.value)


if __name__ == "__main__":
    unittest.main()
