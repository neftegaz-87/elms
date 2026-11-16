"""Behavior contracts for the B2C admission profile boundary."""

from __future__ import annotations

import base64
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import frappe

from elms.admission import api, profile
from elms.elms_core.doctype.elms_admission_profile import elms_admission_profile as admission_doctype
from elms.admission.schemas import LearnerProfile, parse_learner_profile


def profile_payload(**overrides):
    payload = {
        "fio_first_name": "Иван",
        "fio_last_name": "Петров",
        "fio_middle_name": "Сергеевич",
        "birth_date": "1990-02-03",
        "passport_series": "4501",
        "passport_number": "123456",
        "snils": "123-456-789 00",
        "education_level": "higher",
        "profession": "Инженер",
        "phone": "+79990000000",
        "consent_version": "pd-2026-01",
        "passport_scan": {"file_name": "passport.pdf", "content": base64.b64encode(b"passport").decode()},
        "snils_scan": {"file_name": "snils.pdf", "content": base64.b64encode(b"snils").decode()},
        "education_doc_scan": {"file_name": "education.pdf", "content": base64.b64encode(b"education").decode()},
    }
    payload.update(overrides)
    return payload


class FakeProfile(SimpleNamespace):
    name = "ADMISSION-1"

    def __init__(self, **values):
        super().__init__(**values)
        self.flags = SimpleNamespace()
        self._new = True

    def update(self, values):
        self.__dict__.update(values)

    def is_new(self):
        return self._new

    def insert(self, **kwargs):
        self._new = False
        return self

    def save(self, **kwargs):
        self._new = False
        return self


class TestLearnerProfileSchema(unittest.TestCase):
    def test_complete_profile_is_typed_and_normalized(self):
        value = parse_learner_profile(profile_payload())

        self.assertIsInstance(value, LearnerProfile)
        self.assertEqual(value.fio_first_name, "Иван")
        self.assertEqual(value.passport_scan.file_name, "passport.pdf")

    def test_missing_scan_or_consent_is_rejected_before_persistence(self):
        with self.assertRaises(ValueError):
            parse_learner_profile(profile_payload(snils_scan=None))
        with self.assertRaises(ValueError):
            parse_learner_profile(profile_payload(consent_version=""))

    def test_save_incomplete_profile_raises_frappe_validation_error_before_persistence(self):
        with (
            patch.object(profile.frappe, "session", SimpleNamespace(user="learner@example.test"), create=True),
            patch.object(profile.frappe, "get_roles", return_value=["ELMS Learner"], create=True),
            patch.object(profile.frappe, "new_doc", side_effect=AssertionError("profile must not persist"), create=True),
        ):
            with self.assertRaises(frappe.ValidationError):
                profile.save_admission_profile(profile_payload(education_doc_scan=None))


class TestAdmissionProfilePersistence(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()
        self.db.exists.return_value = False
        self.doc = FakeProfile()
        self.saved_files = []

    def _new_doc(self, doctype):
        self.assertEqual(doctype, "ELMS Admission Profile")
        return self.doc

    def _save_file(self, filename, content, dt, dn, **kwargs):
        self.saved_files.append(
            {"file_name": filename, "content": content, "doctype": dt, "docname": dn, **kwargs}
        )
        return SimpleNamespace(name=f"FILE-{len(self.saved_files)}", file_name=filename, is_private=1)

    def test_complete_profile_upserts_one_document_and_private_files(self):
        with (
            patch.object(profile.frappe, "db", self.db, create=True),
            patch.object(profile.frappe, "session", SimpleNamespace(user="learner@example.test"), create=True),
            patch.object(profile.frappe, "get_roles", return_value=["ELMS Learner"], create=True),
            patch.object(profile.frappe, "get_doc", return_value=SimpleNamespace(email="learner@example.test"), create=True),
            patch.object(profile.frappe, "new_doc", side_effect=self._new_doc, create=True),
            patch.object(profile, "save_file", side_effect=self._save_file),
        ):
            result = profile.save_admission_profile(profile_payload())

        self.assertEqual(result["name"], "ADMISSION-1")
        self.assertTrue(result["complete"])
        self.assertEqual(len(self.saved_files), 3)
        self.assertTrue(all(item["is_private"] == 1 for item in self.saved_files))
        self.assertTrue(all(item["doctype"] == "ELMS Admission Profile" for item in self.saved_files))
        self.assertEqual(self.doc.user, "learner@example.test")
        self.assertEqual(self.doc.consent_version, "pd-2026-01")

    def test_profile_update_replaces_previous_private_files_and_keeps_consent_time(self):
        self.db.exists.return_value = "ADMISSION-1"
        self.doc = FakeProfile(
            user="learner@example.test",
            consent_version="pd-2026-01",
            consent_timestamp="2026-11-16 10:00:00",
        )
        old_files = [
            {"name": "OLD-PASSPORT", "attached_to_field": "passport_scan"},
            {"name": "OLD-SNILS", "attached_to_field": "snils_scan"},
            {"name": "OLD-EDUCATION", "attached_to_field": "education_doc_scan"},
        ]

        with (
            patch.object(profile.frappe, "db", self.db, create=True),
            patch.object(profile.frappe, "session", SimpleNamespace(user="learner@example.test"), create=True),
            patch.object(profile.frappe, "get_roles", return_value=["ELMS Learner"], create=True),
            patch.object(profile.frappe, "get_doc", return_value=self.doc, create=True),
            patch.object(profile.frappe, "get_all", return_value=old_files, create=True),
            patch.object(profile.frappe, "delete_doc", create=True) as delete_doc,
            patch.object(profile, "save_file", side_effect=self._save_file),
            patch.object(profile, "_now", return_value="2026-11-16 11:00:00"),
        ):
            result = profile.save_admission_profile(profile_payload())

        self.assertEqual(result["name"], "ADMISSION-1")
        self.assertEqual(self.doc.consent_timestamp, "2026-11-16 10:00:00")
        deleted_names = [call.args[1] for call in delete_doc.call_args_list]
        self.assertEqual(deleted_names, ["OLD-PASSPORT", "OLD-SNILS", "OLD-EDUCATION"])

    def test_foreign_profile_is_denied_and_private_urls_are_not_returned(self):
        foreign = FakeProfile(user="other@example.test", passport_scan="/private/files/passport.pdf")
        with (
            patch.object(profile.frappe, "session", SimpleNamespace(user="learner@example.test"), create=True),
            patch.object(profile.frappe, "get_roles", return_value=["ELMS Learner"], create=True),
            patch.object(profile.frappe, "db", self.db, create=True),
            patch.object(profile.frappe, "get_doc", return_value=foreign, create=True),
        ):
            with self.assertRaises(frappe.PermissionError):
                profile.read_admission_profile("ADMISSION-1", user="other@example.test")

    def test_profile_log_context_masks_pii(self):
        context = profile.safe_log_context("learner@example.test", profile_payload())

        self.assertNotIn("123456", str(context))
        self.assertNotIn("123-456-789 00", str(context))
        self.assertNotIn("passport", str(context))
        self.assertEqual(context["user"], "le***@example.test")

    def test_doctype_permission_allows_owner_and_read_only_manager(self):
        own = SimpleNamespace(user="learner@example.test")
        foreign = SimpleNamespace(user="other@example.test")
        with patch.object(admission_doctype.frappe, "get_roles", side_effect=lambda user: {
            "learner@example.test": ["ELMS Learner"],
            "ops@example.test": ["ELMS Operations User"],
        }.get(user, []), create=True):
            self.assertTrue(admission_doctype.has_permission(own, "write", "learner@example.test"))
            self.assertFalse(admission_doctype.has_permission(foreign, "read", "learner@example.test"))
            self.assertTrue(admission_doctype.has_permission(own, "read", "ops@example.test"))
            self.assertFalse(admission_doctype.has_permission(own, "write", "ops@example.test"))

    def test_admission_file_permission_scopes_read_access_and_preserves_fallback(self):
        admission_file = SimpleNamespace(
            attached_to_doctype="ELMS Admission Profile",
            attached_to_name="ADMISSION-1",
        )
        other_file = SimpleNamespace(
            attached_to_doctype="Other DocType",
            attached_to_name="OTHER-1",
        )
        roles = {
            "owner@example.test": ["ELMS Learner"],
            "foreign@example.test": ["ELMS Learner"],
            "ops@example.test": ["ELMS Operations User"],
        }
        self.db.get_value.return_value = "owner@example.test"
        with (
            patch.object(profile.frappe, "db", self.db, create=True),
            patch.object(profile.frappe, "get_roles", side_effect=lambda user: roles.get(user, []), create=True),
        ):
            self.assertTrue(profile.has_file_permission(admission_file, "read", "owner@example.test"))
            self.assertFalse(profile.has_file_permission(admission_file, "read", "foreign@example.test"))
            self.assertTrue(profile.has_file_permission(admission_file, "read", "ops@example.test"))
            self.assertFalse(profile.has_file_permission(admission_file, "read", "Guest"))
            self.assertIsNone(profile.has_file_permission(other_file, "read", "foreign@example.test"))


class TestAdmissionAPI(unittest.TestCase):
    def test_guest_cannot_save_profile(self):
        with patch.object(api.frappe, "session", SimpleNamespace(user="Guest"), create=True):
            with self.assertRaises(frappe.PermissionError):
                api.save_profile(profile_payload())


if __name__ == "__main__":
    unittest.main()
