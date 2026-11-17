"""Contracts for the server-owned B2C enrollment payment gate."""

from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import frappe

from elms.admission import enforce
from elms.admission.schemas import PaymentStatus
from elms.lms import api as lms_api


if not hasattr(frappe, "ValidationError"):
    frappe.ValidationError = ValueError
if not hasattr(frappe, "PermissionError"):
    frappe.PermissionError = PermissionError
if not hasattr(frappe, "DoesNotExistError"):
    frappe.DoesNotExistError = LookupError


class TestAdmissionEnrollGate(unittest.TestCase):
    def test_unpaid_b2c_enrollment_is_denied(self):
        db = MagicMock()
        db.get_value.return_value = None

        with patch.object(enforce.frappe, "db", db, create=True):
            with self.assertRaises(frappe.ValidationError):
                enforce.require_paid_payment("learner@example.test", "BATCH-1")

        db.get_value.assert_called_once_with(
            "ELMS Payment",
            {"user": "learner@example.test", "batch": "BATCH-1", "status": PaymentStatus.PAID.value},
            "name",
        )

    def test_paid_payment_allows_b2c_enrollment(self):
        db = MagicMock()
        db.get_value.return_value = "PAYMENT-1"

        with patch.object(enforce.frappe, "db", db, create=True):
            self.assertIsNone(enforce.require_paid_payment("learner@example.test", "BATCH-1"))

    def test_available_b2b_subscription_is_the_only_payment_bypass(self):
        db = MagicMock()
        db.exists.return_value = True
        subscription = SimpleNamespace(status="Active", seats_used=0, total_seats=1)

        with (
            patch.object(enforce.frappe, "db", db, create=True),
            patch.object(enforce.frappe, "get_doc", return_value=subscription, create=True),
        ):
            self.assertIsNone(
                enforce.require_paid_payment(
                    "learner@example.test", "BATCH-1", subscription="SUB-1"
                )
            )

        db.get_value.assert_not_called()

    def test_invalid_subscription_does_not_bypass_unpaid_gate(self):
        db = MagicMock()
        db.exists.return_value = False
        db.get_value.return_value = None

        with patch.object(enforce.frappe, "db", db, create=True):
            with self.assertRaises(frappe.ValidationError):
                enforce.require_paid_payment(
                    "learner@example.test", "BATCH-1", subscription="SUB-1"
                )

    def test_admin_cannot_mark_b2c_enrollment_paid_locally(self):
        db = MagicMock()
        db.exists.return_value = True
        db.get_value.return_value = None

        with (
            patch.object(lms_api.frappe, "session", SimpleNamespace(user="admin@example.test"), create=True),
            patch.object(lms_api.frappe, "db", db, create=True),
            patch.object(lms_api, "_has_role", return_value=True),
        ):
            with self.assertRaises(frappe.ValidationError):
                lms_api.enroll_learner(
                    user="learner@example.test",
                    batch="BATCH-1",
                )


if __name__ == "__main__":
    unittest.main()
