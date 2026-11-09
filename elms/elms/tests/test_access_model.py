"""Contract tests for the ELMS access model and admin settings surface."""

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import frappe

try:
    from frappe.tests.utils import FrappeTestCase
except (ImportError, ModuleNotFoundError):
    FrappeTestCase = unittest.TestCase

from elms.install import (
    ELMS_LEARNER_ROLE,
    GROUP_POLICIES,
    ROLE_PROFILES,
    ensure_permission_manager_access,
    ensure_role_profiles,
    ensure_user_groups,
)
from elms.permissions import get_role_profile_summary
from elms.desk.workspaces import ELMS_WORKSPACE_DEFINITIONS


class TestAccessModelContract(unittest.TestCase):
    def test_learner_name_is_canonical_and_profiles_are_product_bundles(self):
        self.assertEqual(ELMS_LEARNER_ROLE, "ELMS Learner")
        self.assertNotIn("ELMS LMS User", ELMS_LEARNER_ROLE)
        self.assertEqual(ROLE_PROFILES["ELMS Learner Profile"], ("Desk User", "ELMS Learner"))
        self.assertNotIn("System Manager", ROLE_PROFILES["ELMS Admin Profile"])

    def test_settings_surface_contains_matrix_and_record_restrictions(self):
        settings = next(item for item in ELMS_WORKSPACE_DEFINITIONS if item["name"] == "Settings")
        links = {(doctype, label) for _, doctype, label in settings["links"]}
        self.assertIn(("permission-manager", "Матрица прав ролей"), links)
        self.assertIn(("User Permission", "Ограничения пользователей"), links)

    def test_group_policy_explicitly_does_not_grant_roles(self):
        self.assertEqual(len(GROUP_POLICIES), 5)
        self.assertTrue(all("не" in limitation for _, limitation in GROUP_POLICIES.values()))

    def test_permission_manager_page_adds_elms_admin_idempotently(self):
        page = MagicMock()
        page.roles = [SimpleNamespace(role="System Manager")]
        db = MagicMock()
        db.exists.return_value = True
        with patch.object(frappe, "db", db, create=True), patch.object(frappe, "get_doc", return_value=page, create=True):
            ensure_permission_manager_access()
        page.append.assert_called_once_with("roles", {"role": "ELMS Admin"})
        page.save.assert_called_once()

    def test_role_profile_summary_exposes_roles_permissions_and_users(self):
        profile = SimpleNamespace(
            name="ELMS Learner Profile",
            roles=[SimpleNamespace(role="Desk User"), SimpleNamespace(role="ELMS Learner")],
        )
        permission = {"parent": "ELMS LMS Section", "permlevel": 0, "read": 1, "write": 1, "create": 0, "delete": 0}
        with (
            patch("elms.permissions._require_access"),
            patch.object(frappe, "get_doc", return_value=profile, create=True),
            patch("elms.permissions.get_all_perms", return_value=[permission]),
            patch.object(frappe, "get_all", return_value=[{"name": "learner@example.com", "full_name": "Learner"}], create=True),
        ):
            summary = get_role_profile_summary("ELMS Learner Profile")
        self.assertEqual([role["name"] for role in summary["roles"]], ["Desk User", "ELMS Learner"])
        self.assertEqual(summary["permissions"][0]["rights"], ["read", "write"])
        self.assertEqual(summary["users"][0]["name"], "learner@example.com")


class TestPermissionManagerRuntime(FrappeTestCase):
    def test_elms_admin_can_open_permission_manager_bridge(self):
        from elms.permissions import get_roles_and_doctypes

        user = "elms.test.admin@elms.local"
        if not hasattr(self, "set_user") or not hasattr(frappe, "db") or not frappe.db.exists("User", user):
            self.skipTest("Requires the seeded ELMS admin user")
        with self.set_user(user):
            result = get_roles_and_doctypes()
        self.assertIn("roles", result)
        self.assertIn("doctypes", result)

    def test_elms_admin_can_read_seeded_profile_explanation(self):
        from elms.permissions import get_role_profile_summary

        user = "elms.test.admin@elms.local"
        if not hasattr(self, "set_user") or not hasattr(frappe, "db") or not frappe.db.exists("User", user):
            self.skipTest("Requires the seeded ELMS admin user")
        with self.set_user(user):
            summary = get_role_profile_summary("ELMS Learner Profile")
        self.assertEqual(summary["name"], "ELMS Learner Profile")
        self.assertIn("ELMS Learner", [role["name"] for role in summary["roles"]])

    def test_learner_cannot_open_permission_manager_bridge(self):
        from elms.permissions import get_roles_and_doctypes

        user = "_elms_access_learner@example.com"
        if not hasattr(self, "set_user") or not hasattr(frappe, "db"):
            self.skipTest("Requires Frappe runtime")
        if not frappe.db.exists("User", user):
            frappe.get_doc(
                {
                    "doctype": "User",
                    "email": user,
                    "first_name": "Access Learner",
                    "enabled": 1,
                    "send_welcome_email": 0,
                    "roles": [{"role": "Desk User"}, {"role": "ELMS Learner"}],
                }
            ).insert(ignore_permissions=True)
            self.addCleanup(frappe.delete_doc, "User", user, force=True, ignore_permissions=True)
        with self.set_user(user):
            with self.assertRaises(frappe.PermissionError):
                get_roles_and_doctypes()


if __name__ == "__main__":
    unittest.main()
