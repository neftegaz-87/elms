"""Contracts for the organization-scoped company cabinet roster."""

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import frappe

from elms.cabinet import api
from elms.cabinet import roster


class TestCabinetRoster(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()
        self.db.exists.return_value = True
        self.db.count.return_value = 1
        self._db_patch = patch.object(roster.frappe, "db", self.db, create=True)
        self._db_patch.start()
        self._user_patch = patch.object(
            roster.frappe,
            "session",
            SimpleNamespace(user="admin-a@example.test"),
            create=True,
        )
        self._user_patch.start()

    def tearDown(self):
        self._user_patch.stop()
        self._db_patch.stop()

    def test_roster_returns_only_members_of_authorized_org_with_progress_join(self):
        def get_all(doctype, **kwargs):
            if doctype == "ELMS Organization Member":
                return [{"user": "learner-a@example.test", "role_profile": "ELMS Learner Profile"}]
            if doctype == "User":
                return [
                    {
                        "name": "learner-a@example.test",
                        "email": "learner-a@example.test",
                        "first_name": "Алексей",
                        "last_name": "А",
                        "full_name": "Алексей А",
                        "enabled": 1,
                    }
                ]
            if doctype == "ELMS Enrollment":
                return [
                    {
                        "name": "enrollment-a",
                        "user": "learner-a@example.test",
                        "course": "course-a",
                        "course_name": "Охрана труда",
                        "status": "Active",
                    },
                    {
                        "name": "enrollment-without-progress",
                        "user": "learner-a@example.test",
                        "course": "course-b",
                        "course_name": "Пожарная безопасность",
                        "status": "Completed",
                    },
                ]
            if doctype == "ELMS Course Progress":
                return [{"enrollment": "enrollment-a", "progress_percentage": 40.0, "completion_date": None}]
            raise AssertionError(f"Unexpected doctype: {doctype}")

        with (
            patch.object(roster.frappe, "get_all", side_effect=get_all, create=True),
            patch.object(roster, "require_organization_access", return_value="org-a"),
            patch.object(roster, "_organization_exists", return_value=True),
        ):
            result = api.get_org_roster("org-a")

        self.assertEqual(result["organization"], "org-a")
        self.assertEqual(result["total"], 1)
        self.assertEqual([row["user"] for row in result["rows"]], ["learner-a@example.test"])
        enrollments = result["rows"][0]["enrollments"]
        self.assertEqual(enrollments[0]["status"], "Active")
        self.assertEqual(enrollments[0]["progress_pct"], 40.0)
        self.assertEqual(enrollments[1]["progress_pct"], 0.0)

    def test_foreign_org_is_denied_by_server_authorization(self):
        with (
            patch.object(roster, "_organization_exists", return_value=True),
            patch.object(roster, "require_organization_access", side_effect=frappe.PermissionError("denied")),
        ):
            with self.assertRaises(frappe.PermissionError):
                api.get_org_roster("org-b")

    def test_page_size_is_bounded_and_empty_org_is_explicit(self):
        with self.assertRaises(frappe.ValidationError):
            api.get_org_roster("org-a", page_size=501)

        with (
            patch.object(roster.frappe, "get_all", return_value=[], create=True),
            patch.object(roster, "_member_count", return_value=0),
            patch.object(roster, "require_organization_access", return_value="org-a"),
            patch.object(roster, "_organization_exists", return_value=True),
        ):
            result = api.get_org_roster("org-a")

        self.assertEqual(result["total"], 0)
        self.assertEqual(result["rows"], [])
        self.assertEqual(result["empty"], True)


if __name__ == "__main__":
    unittest.main()
