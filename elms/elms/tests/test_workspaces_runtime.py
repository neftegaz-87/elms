"""Runtime acceptance tests for ELMS workspace visibility."""

import unittest
import pytest

try:
    import frappe
    from frappe.tests.utils import FrappeTestCase
except (ImportError, ModuleNotFoundError):
    FrappeTestCase = unittest.TestCase
    has_frappe_test = False
else:
    has_frappe_test = True


@pytest.mark.skipif(not has_frappe_test, reason="Requires Frappe test framework runtime")
class TestELMSWorkspaceRuntime(FrappeTestCase):
    def setUp(self):
        if not has_frappe_test:
            self.skipTest("Requires Frappe test framework runtime")
        self.user = "_elms_lms_workspace_test@example.com"
        if not frappe.db.exists("User", self.user):
            frappe.get_doc(
                {
                    "doctype": "User",
                    "email": self.user,
                    "first_name": "ELMS LMS Workspace Test",
                    "enabled": 1,
                    "send_welcome_email": 0,
                    "roles": [{"role": "Desk User"}, {"role": "ELMS LMS User"}],
                }
            ).insert(ignore_permissions=True)
            self.addCleanup(frappe.delete_doc, "User", self.user, force=True, ignore_permissions=True)

    def test_administrator_sees_only_elms_workspaces(self):
        from frappe.desk.desktop import get_workspace_sidebar_items

        with self.set_user("Administrator"):
            names = [page["name"] for page in get_workspace_sidebar_items()["pages"]]

        self.assertEqual(names, ["LMS", "Operations", "Settings"])

    def test_lms_user_sees_only_lms_workspace(self):
        from frappe.desk.desktop import get_workspace_sidebar_items

        with self.set_user(self.user):
            names = [page["name"] for page in get_workspace_sidebar_items()["pages"]]

        self.assertEqual(names, ["LMS"])
