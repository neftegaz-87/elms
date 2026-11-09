"""Runtime acceptance tests for ELMS workspace visibility."""

import unittest

try:
    import frappe
    from frappe.tests.utils import FrappeTestCase
except (ImportError, ModuleNotFoundError):
    FrappeTestCase = unittest.TestCase
    has_frappe_test = False
else:
    has_frappe_test = True


@unittest.skipUnless(has_frappe_test, "Requires Frappe test framework runtime")
class TestELMSWorkspaceRuntime(FrappeTestCase):
    def setUp(self):
        if not has_frappe_test:
            self.skipTest("Requires Frappe test framework runtime")
        self.user = "_elms_lms_workspace_test@example.com"
        self.methodologist = "_elms_methodologist_workspace_test@example.com"
        self.system_manager = "_elms_system_manager_workspace_test@example.com"
        if not frappe.db.exists("User", self.user):
            frappe.get_doc(
                {
                    "doctype": "User",
                    "email": self.user,
                    "first_name": "ELMS LMS Workspace Test",
                    "enabled": 1,
                    "send_welcome_email": 0,
                    "roles": [{"role": "Desk User"}, {"role": "ELMS Learner"}],
                }
            ).insert(ignore_permissions=True)
            self.addCleanup(frappe.delete_doc, "User", self.user, force=True, ignore_permissions=True)
        if not frappe.db.exists("User", self.methodologist):
            frappe.get_doc(
                {
                    "doctype": "User",
                    "email": self.methodologist,
                    "first_name": "ELMS Methodologist Workspace Test",
                    "enabled": 1,
                    "send_welcome_email": 0,
                    "roles": [{"role": "Desk User"}, {"role": "ELMS Methodologist"}],
                }
            ).insert(ignore_permissions=True)
            self.addCleanup(frappe.delete_doc, "User", self.methodologist, force=True, ignore_permissions=True)
        if not frappe.db.exists("User", self.system_manager):
            frappe.get_doc(
                {
                    "doctype": "User",
                    "email": self.system_manager,
                    "first_name": "ELMS System Manager Workspace Test",
                    "enabled": 1,
                    "send_welcome_email": 0,
                    "roles": [{"role": "Desk User"}, {"role": "System Manager"}],
                }
            ).insert(ignore_permissions=True)
            self.addCleanup(frappe.delete_doc, "User", self.system_manager, force=True, ignore_permissions=True)

    def test_administrator_sees_only_elms_workspaces(self):
        from frappe.desk.desktop import get_workspace_sidebar_items

        with self.set_user("Administrator"):
            names = [page["name"] for page in get_workspace_sidebar_items()["pages"]]

        self.assertEqual(names, ["LMS", "Предпросмотр курсов", "Settings"])

    def test_lms_user_sees_only_lms_workspace(self):
        from frappe.desk.desktop import get_workspace_sidebar_items

        with self.set_user(self.user):
            names = [page["name"] for page in get_workspace_sidebar_items()["pages"]]

        self.assertEqual(names, ["LMS"])

    def test_system_manager_sees_settings_workspace(self):
        from frappe.desk.desktop import get_workspace_sidebar_items

        with self.set_user(self.system_manager):
            names = [page["name"] for page in get_workspace_sidebar_items()["pages"]]

        self.assertEqual(names, ["Settings"])

    def test_methodologist_sees_lms_and_preview_only(self):
        from frappe.desk.desktop import get_workspace_sidebar_items

        with self.set_user(self.methodologist):
            names = [page["name"] for page in get_workspace_sidebar_items()["pages"]]

        self.assertEqual(names, ["LMS", "Предпросмотр курсов"])

    def test_operations_user_sees_learning_management(self):
        operations_user = "_elms_operations_workspace_test@example.com"
        if not frappe.db.exists("User", operations_user):
            frappe.get_doc(
                {
                    "doctype": "User",
                    "email": operations_user,
                    "first_name": "ELMS Operations Workspace Test",
                    "enabled": 1,
                    "send_welcome_email": 0,
                    "roles": [{"role": "Desk User"}, {"role": "ELMS Operations User"}],
                }
            ).insert(ignore_permissions=True)
            self.addCleanup(frappe.delete_doc, "User", operations_user, force=True, ignore_permissions=True)

        from frappe.desk.desktop import get_workspace_sidebar_items

        with self.set_user(operations_user):
            names = [page["name"] for page in get_workspace_sidebar_items()["pages"]]

        self.assertEqual(names, ["LMS", "Предпросмотр курсов"])

    def test_installed_lms_workspace_has_no_direct_child_authoring_links(self):
        workspace = frappe.get_doc("Workspace", "LMS")
        link_to = [link.get("link_to") for link in (workspace.get("links") or []) if link.get("type") == "Link"]
        self.assertNotIn("ELMS Course Chapter", link_to)
        self.assertNotIn("ELMS Course Lesson", link_to)
