"""Comprehensive contract and behavior test suite for ELMS Core Learning Flows (LMS)."""

from __future__ import annotations

import json
import os
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import frappe

# Setup mock attributes on frappe if running standalone
if not hasattr(frappe, "throw"):
    def _throw(msg, exc=Exception, *args, **kwargs):
        raise exc(msg)
    frappe.throw = _throw

if not hasattr(frappe, "_"):
    frappe._ = lambda msg: msg

if not hasattr(frappe, "whitelist"):
    def _whitelist(*_args, **_kwargs):
        def decorate(function):
            return function
        return decorate
    frappe.whitelist = _whitelist

if not hasattr(frappe, "session"):
    frappe.session = SimpleNamespace(user="Guest")

if not hasattr(frappe, "db"):
    frappe.db = MagicMock()
if not hasattr(frappe, "new_doc"):
    frappe.new_doc = MagicMock()
if not hasattr(frappe, "get_doc"):
    frappe.get_doc = MagicMock()
if not hasattr(frappe, "get_all"):
    frappe.get_all = MagicMock()

if not hasattr(frappe, "ValidationError"):
    class ValidationError(Exception):
        pass
    frappe.ValidationError = ValidationError

if not hasattr(frappe, "DoesNotExistError"):
    class DoesNotExistError(Exception):
        pass
    frappe.DoesNotExistError = DoesNotExistError

if not hasattr(frappe, "PermissionError"):
    class PermissionError(Exception):
        pass
    frappe.PermissionError = PermissionError

if hasattr(frappe, "utils"):
    if not hasattr(frappe.utils, "today"):
        frappe.utils.today = lambda: "2026-11-05"
    if not hasattr(frappe.utils, "now_datetime"):
        frappe.utils.now_datetime = lambda: "2026-11-05 12:00:00"
else:
    frappe.utils = SimpleNamespace(
        today=lambda: "2026-11-05",
        now_datetime=lambda: "2026-11-05 12:00:00",
    )

import elms.lms.api as lms_api
from elms.desk.workspaces import ELMS_WORKSPACE_DEFINITIONS


class FakeDoc(dict):
    """Simple dict wrapper simulating Frappe Document behavior in tests."""
    def __init__(self, doctype: str, **kwargs):
        super().__init__(**kwargs)
        self.doctype = doctype
        self.name = kwargs.get("name") or f"{doctype.lower().replace(' ', '_')}_{len(kwargs) + 1}"
        self.flags = SimpleNamespace(ignore_permissions=False)
        self._is_new = kwargs.get("_is_new", False)

    def is_new(self) -> bool:
        return getattr(self, "_is_new", False)

    def __getattr__(self, item: str):
        return self.get(item)

    def __setattr__(self, key: str, value):
        if key in ("doctype", "name", "flags", "_is_new"):
            super().__setattr__(key, value)
        else:
            self[key] = value

    def insert(self):
        self._is_new = False
        return self

    def save(self):
        return self


class TestLMSCoreFlows(unittest.TestCase):
    def setUp(self):
        frappe.session.user = "student@example.ru"

    def test_lms_doctypes_registered(self):
        """FR-001 / TM-001: Check that all 7 LMS DocTypes are created with valid schemas."""
        base_dir = Path(__file__).resolve().parent.parent / "lms" / "doctype"
        expected = [
            "elms_batch",
            "elms_subscription",
            "elms_enrollment",
            "elms_course_progress",
            "elms_lesson_progress",
            "elms_user_activity",
            "elms_video_watch_log",
        ]
        for name in expected:
            dt_dir = base_dir / name
            self.assertTrue(dt_dir.exists(), f"DocType directory {name} does not exist")
            json_file = dt_dir / f"{name}.json"
            self.assertTrue(json_file.exists(), f"Manifest {json_file} does not exist")
            data = json.loads(json_file.read_text(encoding="utf-8"))
            self.assertEqual(data.get("module"), "LMS")
            self.assertGreater(len(data.get("fields", [])), 2)
            self.assertGreater(len(data.get("permissions", [])), 0)

    def test_lms_subscription_quota_enforcement(self):
        """FR-001, FR-002 / TM-002: Verify seat quota tracking and overflow rejection."""
        sub_doc = FakeDoc(
            "ELMS Subscription",
            name="SUB-001",
            company_name="Gazprom",
            inn="7700000000",
            total_seats=2,
            seats_used=0,
            status="Active",
        )

        with patch.object(frappe.db, "exists", return_value=True), \
             patch.object(frappe.db, "get_value", return_value=None), \
             patch.object(frappe, "get_doc", return_value=sub_doc), \
             patch.object(frappe, "new_doc", side_effect=lambda dt: FakeDoc(dt, _is_new=True)), \
             patch.object(lms_api, "_has_role", return_value=True):

            # First enrollment succeeds
            res1 = lms_api.enroll_learner(user="u1@example.ru", batch="BATCH-1", subscription="SUB-001")
            self.assertEqual(sub_doc.seats_used, 1)
            self.assertEqual(sub_doc.status, "Active")

            # Second enrollment succeeds and exhausts quota
            res2 = lms_api.enroll_learner(user="u2@example.ru", batch="BATCH-1", subscription="SUB-001")
            self.assertEqual(sub_doc.seats_used, 2)
            self.assertEqual(sub_doc.status, "Exhausted")

            # Third enrollment must raise ValidationError (Quota exhausted)
            with self.assertRaises(frappe.ValidationError):
                lms_api.enroll_learner(user="u3@example.ru", batch="BATCH-1", subscription="SUB-001")

    def test_lms_enrollment_lifecycle(self):
        """FR-002 / TM-003: Verify successful enrollment and course progress creation."""
        created_docs = []
        def fake_factory(dt):
            d = FakeDoc(dt, _is_new=True)
            created_docs.append(d)
            return d

        with patch.object(frappe.db, "exists", return_value=True), \
             patch.object(frappe.db, "get_value", return_value=None), \
             patch.object(frappe, "new_doc", side_effect=fake_factory), \
             patch.object(lms_api, "_has_role", return_value=True):

            res = lms_api.enroll_learner(user="student@example.ru", batch="BATCH-2026")
            self.assertIn("enrollment", res)
            self.assertEqual(res["status"], "Active")
            self.assertIn("course_progress", res)

            # Verify both Enrollment and Course Progress were created
            types = [d.doctype for d in created_docs]
            self.assertIn("ELMS Enrollment", types)
            self.assertIn("ELMS Course Progress", types)

    def test_lms_duplicate_enrollment_rejected(self):
        """BN-006 / TM-004: Duplicate active enrollment must be rejected."""
        with patch.object(frappe.db, "exists", return_value=True), \
             patch.object(frappe.db, "get_value", return_value="ENR-EXISTING"), \
             patch.object(lms_api, "_has_role", return_value=True):

            with self.assertRaises(frappe.ValidationError):
                lms_api.enroll_learner(user="student@example.ru", batch="BATCH-2026")

    def test_lms_record_lesson_progress(self):
        """FR-002 / TM-005: Verify recording lesson heartbeat and completion."""
        cp_doc = FakeDoc(
            "ELMS Course Progress",
            name="CP-001",
            enrollment="ENR-001",
            user="student@example.ru",
            total_lessons=1,
            completed_lessons=0,
            progress_percentage=0.0,
            exam_eligible=0,
        )

        lp_doc = FakeDoc(
            "ELMS Lesson Progress",
            name="LP-001",
            course_progress="CP-001",
            lesson_id="lesson-01",
            time_spent_seconds=60,
            is_completed=0,
            _is_new=False,
        )

        def get_val_side_effect(dt, filters, field):
            if dt == "ELMS Enrollment":
                return "student@example.ru"
            if dt == "ELMS Course Progress":
                return "CP-001"
            if dt == "ELMS Lesson Progress":
                return "LP-001"
            return None

        def get_doc_side_effect(dt, name):
            if dt == "ELMS Lesson Progress":
                return lp_doc
            if dt == "ELMS Course Progress":
                return cp_doc
            return FakeDoc(dt)

        with patch.object(frappe.db, "exists", return_value=True), \
             patch.object(frappe.db, "get_value", side_effect=get_val_side_effect), \
             patch.object(frappe, "get_doc", side_effect=get_doc_side_effect), \
             patch.object(frappe, "get_all", return_value=[{"is_completed": 1, "time_spent_seconds": 120}]), \
             patch.object(lms_api, "_has_role", return_value=False):

            res = lms_api.record_lesson_progress(
                enrollment="ENR-001",
                lesson_id="lesson-01",
                time_spent_delta=60,
                mark_completed=True,
            )

            self.assertEqual(res["lesson_id"], "lesson-01")
            self.assertEqual(res["is_completed"], 1)
            self.assertEqual(res["total_time_spent_seconds"], 120)
            self.assertEqual(res["course_progress_percentage"], 100.0)
            self.assertEqual(res["exam_eligible"], 1)

    def test_lms_heartbeat_boundary_guard(self):
        """BN-003 / TM-006: Heartbeat delta over 300 seconds or negative must fail."""
        with patch.object(frappe.db, "exists", return_value=True), \
             patch.object(frappe.db, "get_value", return_value="student@example.ru"):

            # Delta > 300 seconds
            with self.assertRaises(frappe.ValidationError):
                lms_api.record_lesson_progress(enrollment="ENR-001", lesson_id="l1", time_spent_delta=301)

            # Negative delta
            with self.assertRaises(frappe.ValidationError):
                lms_api.record_lesson_progress(enrollment="ENR-001", lesson_id="l1", time_spent_delta=-5)

    def test_lms_course_progress_calculation(self):
        """FR-002 / TM-007: Math percentage and exam eligibility rule (100% required)."""
        cp_doc = FakeDoc(
            "ELMS Course Progress",
            name="CP-MATH",
            total_lessons=0,
            completed_lessons=0,
            progress_percentage=0.0,
            exam_eligible=0,
        )

        with patch.object(frappe.db, "exists", return_value=True), \
             patch.object(frappe, "get_doc", return_value=cp_doc), \
             patch.object(frappe, "get_all") as mock_get_all:

            # Case 1: 1 out of 2 completed (50%) -> exam_eligible=0
            mock_get_all.return_value = [
                {"is_completed": 1, "time_spent_seconds": 100},
                {"is_completed": 0, "time_spent_seconds": 50},
            ]
            res1 = lms_api.calculate_course_progress("CP-MATH")
            self.assertEqual(res1["progress_percentage"], 50.0)
            self.assertEqual(res1["exam_eligible"], 0)

            # Case 2: 2 out of 2 completed (100%) -> exam_eligible=1
            mock_get_all.return_value = [
                {"is_completed": 1, "time_spent_seconds": 100},
                {"is_completed": 1, "time_spent_seconds": 120},
            ]
            res2 = lms_api.calculate_course_progress("CP-MATH")
            self.assertEqual(res2["progress_percentage"], 100.0)
            self.assertEqual(res2["exam_eligible"], 1)

    def test_lms_user_activity_telemetry(self):
        """US-LMS-007 / TM-008: 152-FZ immutable activity telemetry record."""
        recorded_docs = []
        def fake_activity(dt):
            d = FakeDoc(dt, _is_new=True)
            recorded_docs.append(d)
            return d

        with patch.object(frappe, "new_doc", side_effect=fake_activity):
            lms_api._record_user_activity("student@example.ru", "Quiz Submit", "ELMS Quiz", "QUIZ-01")

            self.assertEqual(len(recorded_docs), 1)
            act = recorded_docs[0]
            self.assertEqual(act.doctype, "ELMS User Activity")
            self.assertEqual(act.user, "student@example.ru")
            self.assertEqual(act.activity_type, "Quiz Submit")
            self.assertEqual(act.reference_name, "QUIZ-01")

    def test_lms_docperm_and_isolation(self):
        """BN-004, BN-005 / TM-009: Unauthenticated or cross-user calls are denied."""
        # Unauthenticated guest call
        frappe.session.user = "Guest"
        with self.assertRaises(frappe.PermissionError):
            lms_api.enroll_learner(user="student@example.ru", batch="BATCH-1")

        # Cross-user progress update by non-admin
        frappe.session.user = "other_student@example.ru"
        with patch.object(frappe.db, "exists", return_value=True), \
             patch.object(frappe.db, "get_value", return_value="student@example.ru"), \
             patch.object(lms_api, "_has_role", return_value=False):

            with self.assertRaises(frappe.PermissionError):
                lms_api.record_lesson_progress(enrollment="ENR-001", lesson_id="l1", time_spent_delta=30)

    def test_lms_workspace_navigation(self):
        """FR-003 / TM-010: Verify Workspace LMS has cards for Batch, Subscription, Progress, and Section."""
        lms_ws = next((item for item in ELMS_WORKSPACE_DEFINITIONS if item["name"] == "LMS"), None)
        self.assertIsNotNone(lms_ws)
        links = lms_ws["links"]

        doctypes_linked = [link_to for _, link_to, _ in links]
        self.assertIn("ELMS Batch", doctypes_linked)
        self.assertIn("ELMS Subscription", doctypes_linked)
        self.assertIn("ELMS Enrollment", doctypes_linked)
        self.assertIn("ELMS Course Progress", doctypes_linked)
        self.assertIn("ELMS Lesson Progress", doctypes_linked)
        self.assertIn("ELMS User Activity", doctypes_linked)
        self.assertIn("ELMS LMS Section", doctypes_linked)


if __name__ == "__main__":
    unittest.main()
