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
            "elms_quiz",
            "elms_quiz_question",
            "elms_quiz_attempt",
            "elms_program",
            "elms_program_course",
            "elms_program_enrollment",
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
                {"lesson_id": "l1", "is_completed": 1, "time_spent_seconds": 100},
                {"lesson_id": "l2", "is_completed": 0, "time_spent_seconds": 50},
            ]
            res1 = lms_api.calculate_course_progress("CP-MATH")
            self.assertEqual(res1["progress_percentage"], 50.0)
            self.assertEqual(res1["exam_eligible"], 0)

            # Case 2: 2 out of 2 completed (100%) -> exam_eligible=1
            mock_get_all.return_value = [
                {"lesson_id": "l1", "is_completed": 1, "time_spent_seconds": 100},
                {"lesson_id": "l2", "is_completed": 1, "time_spent_seconds": 120},
            ]
            res2 = lms_api.calculate_course_progress("CP-MATH")
            self.assertEqual(res2["progress_percentage"], 100.0)
            self.assertEqual(res2["exam_eligible"], 1)

    def test_lms_course_progress_calculation_matches_syllabus_by_lesson_id(self):
        """Syllabus path must key lesson progress by lesson_id, not drop completed rows."""
        cp_doc = FakeDoc(
            "ELMS Course Progress",
            name="CP-SYL",
            enrollment="ENR-SYL",
            total_lessons=0,
            completed_lessons=0,
            progress_percentage=0.0,
            exam_eligible=0,
        )

        def get_all_side_effect(doctype, *args, **kwargs):
            if doctype == "ELMS Lesson Progress":
                fields = kwargs.get("fields") or []
                self.assertIn("lesson_id", fields)
                return [
                    {"lesson_id": "LESSON-1", "is_completed": 1, "time_spent_seconds": 40},
                    {"lesson_id": "LESSON-2", "is_completed": 0, "time_spent_seconds": 10},
                ]
            if doctype == "ELMS Course Lesson":
                return [{"name": "LESSON-1"}, {"name": "LESSON-2"}]
            return []

        def get_value_side_effect(doctype, name, field=None, *args, **kwargs):
            if doctype == "ELMS Enrollment" and field == "course":
                return "COURSE-1"
            if doctype == "ELMS Enrollment" and field == "batch":
                return None
            if doctype == "ELMS Course" and field == "name":
                return "COURSE-1"
            return None

        with patch.object(frappe.db, "exists", return_value=True), \
             patch.object(frappe, "get_doc", return_value=cp_doc), \
             patch.object(frappe, "get_all", side_effect=get_all_side_effect), \
             patch.object(frappe.db, "get_value", side_effect=get_value_side_effect):
            res = lms_api.calculate_course_progress("CP-SYL")
            self.assertEqual(res["total_lessons"], 2)
            self.assertEqual(res["completed_lessons"], 1)
            self.assertEqual(res["progress_percentage"], 50.0)
            self.assertEqual(res["exam_eligible"], 0)

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
        """FR-003 / TM-010: The shared LMS workspace exposes the authoring surface."""
        lms_ws = next((item for item in ELMS_WORKSPACE_DEFINITIONS if item["name"] == "LMS"), None)
        self.assertIsNotNone(lms_ws)
        link_to = [link[1] for link in lms_ws["links"]]
        self.assertIn("ELMS Course", link_to)
        self.assertNotIn("ELMS Course Chapter", link_to)
        self.assertNotIn("ELMS Course Lesson", link_to)
        self.assertIn("/app/elms-course-studio", [shortcut.get("url") for shortcut in lms_ws["shortcuts"]])
        self.assertIn("ELMS Quiz", link_to)
        self.assertIn("ELMS Quiz Question", link_to)
        self.assertIn("ELMS Course Progress", link_to)

    def test_self_enrollment_requires_active_published_batch(self):
        """A learner may self-enroll only into a published active course batch."""
        frappe.session.user = "student@example.ru"
        with patch.object(frappe.db, "exists", return_value=True), \
             patch.object(frappe.db, "get_value", side_effect=[
                 {"course": "COURSE-1", "status": "Active"},
                 1,
             ]), \
             patch.object(lms_api, "enroll_learner", return_value={"enrollment": "ENR-1"}) as enroll, \
             patch.object(lms_api, "_record_user_activity"):
            result = lms_api.enroll_self("BATCH-1")

        self.assertEqual(result["enrollment"], "ENR-1")
        enroll.assert_called_once_with(user="student@example.ru", batch="BATCH-1")

    def test_quiz_public_payload_hides_correct_answers(self):
        """Learners receive option labels but never the answer key."""
        payload = lms_api._quiz_public_questions([
            {
                "name": "Q-1",
                "question_text": "Вопрос",
                "sequence_id": 1,
                "question_type": "Single Choice",
                "options": [{"id": "A", "text": "Да", "correct": True}],
                "points": 1,
                "topic": "Безопасность",
            }
        ])
        self.assertEqual(payload[0]["options"], [{"id": "A", "text": "Да"}])
        self.assertNotIn("correct", payload[0]["options"][0])

    def test_quiz_options_reject_duplicate_or_empty_values(self):
        """Published quiz questions must have stable, non-empty option contracts."""
        with patch.object(
            frappe,
            "get_all",
            return_value=[{
                "name": "Q-INVALID",
                "question_text": "Вопрос",
                "sequence_id": 1,
                "question_type": "Single Choice",
                "options_json": json.dumps([
                    {"id": "A", "text": "Да"},
                    {"id": "A", "text": "Повтор"},
                ]),
                "points": 1,
            }],
        ):
            with self.assertRaises(frappe.ValidationError):
                lms_api._quiz_questions("QUIZ-INVALID")

    def test_quiz_draft_save_persists_answers_and_counters(self):
        """A learner can save a partial attempt without grading it."""
        attempt = FakeDoc(
            "ELMS Quiz Attempt",
            name="ATTEMPT-DRAFT",
            quiz="QUIZ-1",
            user="student@example.ru",
            status="In Progress",
            deadline_at=None,
            snapshot_json=json.dumps([
                {
                    "name": "Q-1",
                    "question_type": "Single Choice",
                    "options": [{"id": "A", "text": "Да", "correct": True}],
                },
                {
                    "name": "Q-2",
                    "question_type": "Multiple Choice",
                    "options": [{"id": "B", "text": "Б", "correct": False}],
                },
            ]),
        )
        with patch.object(frappe, "get_doc", return_value=attempt), \
             patch.object(lms_api, "_record_user_activity"), \
             patch.object(lms_api, "_now_datetime", return_value="2026-11-12 14:30:00"):
            result = lms_api.save_quiz_progress("ATTEMPT-DRAFT", json.dumps({"Q-1": ["A"]}))

        self.assertEqual(result["answered_questions"], 1)
        self.assertEqual(result["total_questions"], 2)
        self.assertEqual(result["progress_percentage"], 50.0)
        self.assertEqual(json.loads(attempt.answers_json), {"Q-1": ["A"]})
        self.assertEqual(attempt.status, "In Progress")

    def test_start_quiz_resumes_existing_active_attempt(self):
        """Starting the same quiz again returns the saved attempt instead of duplicating it."""
        attempt = FakeDoc(
            "ELMS Quiz Attempt",
            name="ATTEMPT-RESUME",
            quiz="QUIZ-1",
            enrollment="ENR-1",
            user="student@example.ru",
            status="In Progress",
            deadline_at=None,
            answers_json=json.dumps({"Q-1": ["A"]}),
            snapshot_json=json.dumps([{
                "name": "Q-1",
                "question_text": "Вопрос",
                "sequence_id": 1,
                "question_type": "Single Choice",
                "options": [{"id": "A", "text": "Да", "correct": True}],
                "points": 1,
                "topic": "Общие вопросы",
            }]),
        )
        with patch.object(lms_api, "_quiz_for_learner", return_value={"quiz_name": "Тест", "quiz_type": "Practice"}), \
             patch.object(lms_api, "_quiz_questions", return_value=json.loads(attempt.snapshot_json)), \
             patch.object(frappe.db, "get_value", return_value="ATTEMPT-RESUME"), \
             patch.object(frappe, "get_doc", return_value=attempt), \
             patch.object(lms_api, "_record_user_activity"):
            result = lms_api.start_quiz("QUIZ-1", "ENR-1")

        self.assertTrue(result["resumed"])
        self.assertEqual(result["attempt"], "ATTEMPT-RESUME")
        self.assertEqual(result["answered_questions"], 1)

    def test_quiz_invalid_option_is_rejected_before_save(self):
        """Draft persistence cannot introduce option ids outside the frozen snapshot."""
        attempt = FakeDoc(
            "ELMS Quiz Attempt",
            name="ATTEMPT-INVALID",
            quiz="QUIZ-1",
            user="student@example.ru",
            status="In Progress",
            deadline_at=None,
            snapshot_json=json.dumps([{
                "name": "Q-1",
                "question_type": "Single Choice",
                "options": [{"id": "A", "text": "Да", "correct": True}],
            }]),
        )
        with patch.object(frappe, "get_doc", return_value=attempt):
            with self.assertRaises(frappe.ValidationError):
                lms_api.save_quiz_progress("ATTEMPT-INVALID", json.dumps({"Q-1": ["WRONG"]}))

    def test_learner_profile_denies_cross_user_without_source_read_permissions(self):
        """Cross-user history is fail-closed and returns no partial profile."""
        with patch.object(frappe.db, "exists", return_value=True), \
             patch.object(frappe, "has_permission", return_value=False, create=True), \
             patch.object(lms_api, "_record_user_activity"):
            with self.assertRaises(frappe.PermissionError):
                lms_api.get_learner_profile("other@example.ru")

    def test_learner_profile_groups_courses_programs_and_activity_by_year(self):
        """Self profile exposes the canonical LMS learning history projection."""
        def get_value(doctype, name, field, **kwargs):
            if doctype == "User":
                return {"name": "student@example.ru", "full_name": "Иван Слушатель", "email": "student@example.ru"}
            if doctype == "ELMS Batch":
                return {"batch_name": "Поток 2026", "course": "COURSE-1"}
            if doctype == "ELMS Course":
                return "Охрана труда"
            if doctype == "ELMS Course Progress":
                return {"name": "CP-1", "progress_percentage": 50, "total_lessons": 4, "completed_lessons": 2, "total_time_spent_seconds": 900, "exam_eligible": 0, "completion_date": None}
            if doctype == "ELMS Program":
                return {"program_name": "Вводная программа", "program_code": "P-1"}
            return None

        def get_all(doctype, **kwargs):
            if doctype == "ELMS Enrollment":
                return [{"name": "ENR-1", "batch": "BATCH-1", "course": "COURSE-1", "program_enrollment": "PE-1", "enrollment_date": "2026-02-01", "status": "Active", "modified": "2026-02-01"}]
            if doctype == "ELMS Program Enrollment":
                return [{"name": "PE-1", "program": "PROGRAM-1", "enrollment_date": "2026-01-15", "status": "Active", "progress_percentage": 25, "total_courses": 2, "completed_courses": 0, "current_course": "COURSE-1", "modified": "2026-01-15"}]
            if doctype == "ELMS User Activity":
                return [{"name": "ACT-1", "activity_type": "Login", "reference_doctype": "User", "reference_name": "student@example.ru", "timestamp": "2026-02-02 10:00:00"}]
            if doctype == "ELMS Quiz Attempt":
                return []
            return []

        with patch.object(frappe.db, "exists", return_value=True), \
             patch.object(frappe.db, "get_value", side_effect=get_value), \
             patch.object(frappe, "get_all", side_effect=get_all):
            result = lms_api.get_learner_profile()

        self.assertEqual(result["user"]["full_name"], "Иван Слушатель")
        self.assertEqual(result["summary"]["last_login_at"], "2026-02-02 10:00:00")
        self.assertEqual(result["history_by_year"][0]["year"], 2026)
        self.assertEqual(len(result["history_by_year"][0]["courses"]), 1)
        self.assertEqual(len(result["history_by_year"][0]["programs"]), 1)
        self.assertEqual(len(result["history_by_year"][0]["events"]), 1)

    def test_quiz_submission_is_graded_server_side(self):
        """A submitted attempt is closed and scored from its server snapshot."""
        attempt = FakeDoc(
            "ELMS Quiz Attempt",
            name="ATTEMPT-1",
            quiz="QUIZ-1",
            enrollment="ENR-1",
            user="student@example.ru",
            status="In Progress",
            deadline_at=None,
            snapshot_json=json.dumps([
                {
                    "name": "Q-1",
                    "options": [{"id": "A", "correct": True}, {"id": "B", "correct": False}],
                    "points": 1,
                    "topic": "Безопасность",
                }
            ]),
        )
        with patch.object(frappe, "get_doc", return_value=attempt), \
             patch.object(frappe.db, "get_value", side_effect=[80, "LESSON-1", "Practice"]), \
             patch.object(lms_api, "_record_user_activity"):
            result = lms_api.submit_quiz("ATTEMPT-1", json.dumps({"Q-1": ["B"]}))

        self.assertEqual(result["status"], "Failed")
        self.assertEqual(result["score_percentage"], 0.0)
        self.assertEqual(attempt.answers_json, '{"Q-1": ["B"]}')


if __name__ == "__main__":
    unittest.main()
