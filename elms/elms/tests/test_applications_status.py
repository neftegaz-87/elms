"""Contracts for the Bitrix-owned application status boundary."""

from __future__ import annotations

import json
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import frappe

from elms.applications import status


class TestApplicationStatus(unittest.TestCase):
    def test_fetch_reads_only_lead_status_id(self):
        endpoint = SimpleNamespace()
        with patch.object(status, "resolve_webhook_endpoint", return_value=endpoint):
            with patch.object(status, "post_json", return_value=json.dumps({"result": {"STATUS_ID": "STAGE_X"}}).encode()) as post:
                self.assertEqual(status.fetch_bitrix_status("42"), "STAGE_X")
        post.assert_called_once_with(endpoint, "crm.lead.get", {"id": "42"})

    def test_refresh_persists_snapshot_and_mapped_label_after_bitrix_change(self):
        link = SimpleNamespace(name="APP-1", bitrix_id="42", application_kind="individual")
        db = MagicMock()
        with (
            patch.object(frappe, "session", SimpleNamespace(user="operator@example.test"), create=True),
            patch.object(frappe, "get_roles", return_value=["ELMS Operations User"], create=True),
            patch.object(frappe, "get_doc", return_value=link, create=True),
            patch.object(status, "fetch_bitrix_status", return_value="CONVERTED"),
            patch.object(frappe, "db", db, create=True),
        ):
            result = status.refresh_application_status("APP-1")

        self.assertEqual(result["status_code"], "CONVERTED")
        self.assertEqual(result["display_label"], "Обработана")
        self.assertEqual(link.last_status_snapshot, "CONVERTED")
        self.assertEqual(link.last_status_code, "CONVERTED")
        db.set_value.assert_called_once()

    def test_refresh_persists_stage_x_from_bitrix_and_uses_mapping(self):
        link = SimpleNamespace(name="APP-2", bitrix_id="42", application_kind="individual")
        db = MagicMock()
        settings = SimpleNamespace(status_map=json.dumps({"STAGE_X": "На проверке"}))
        with (
            patch.object(frappe, "session", SimpleNamespace(user="operator@example.test"), create=True),
            patch.object(frappe, "get_roles", return_value=["ELMS Operations User"], create=True),
            patch.object(frappe, "get_doc", return_value=link, create=True),
            patch.object(status, "fetch_bitrix_status", return_value="STAGE_X"),
            patch.object(frappe, "get_single", return_value=settings, create=True),
            patch.object(frappe, "db", db, create=True),
        ):
            result = status.refresh_application_status("APP-2")

        self.assertEqual(result["status_code"], "STAGE_X")
        self.assertEqual(result["display_label"], "На проверке")
        self.assertEqual(link.last_status_snapshot, "STAGE_X")
        self.assertEqual(link.last_status_code, "STAGE_X")
        db.set_value.assert_called_once()

    def test_refresh_denies_non_operator_without_calling_bitrix(self):
        with (
            patch.object(frappe, "session", SimpleNamespace(user="learner@example.test"), create=True),
            patch.object(frappe, "get_roles", return_value=["ELMS Learner"], create=True),
            patch.object(status, "fetch_bitrix_status") as fetch,
        ):
            with self.assertRaises(getattr(frappe, "PermissionError", PermissionError)):
                status.refresh_application_status("APP-1")
        fetch.assert_not_called()

    def test_status_map_can_be_customized_without_becoming_a_writeable_status(self):
        settings = SimpleNamespace(status_map=json.dumps({"STAGE_X": "На проверке"}))
        with patch.object(frappe, "get_single", return_value=settings, create=True):
            self.assertEqual(status.status_label("STAGE_X"), "На проверке")


class TestApplicationLinkStatusDeny(unittest.TestCase):
    def test_local_master_status_is_rejected(self):
        from elms_core.doctype.elms_application_link.elms_application_link import ELMSApplicationLink

        doc = ELMSApplicationLink()
        doc.status = "Approved"
        with patch.object(frappe, "ValidationError", ValueError, create=True):
            with patch.object(frappe, "throw", side_effect=ValueError, create=True):
                with self.assertRaises(ValueError):
                    doc.validate()


if __name__ == "__main__":
    unittest.main()
