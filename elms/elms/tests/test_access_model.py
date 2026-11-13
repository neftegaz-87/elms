"""Contract tests for the ELMS access model and admin settings surface."""

import unittest
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import frappe

try:
    from frappe.tests.utils import FrappeTestCase
except (ImportError, ModuleNotFoundError):
    FrappeTestCase = unittest.TestCase

from elms.install import (
    ELMS_COMPANY_ADMIN_ROLE,
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
    def test_organization_doctypes_and_company_admin_contract_exist(self):
        from elms.access import api as access_api

        access_root = Path(__file__).resolve().parents[1] / "elms_core"
        organization = json.loads(
            (access_root / "doctype/elms_organization/elms_organization.json").read_text(encoding="utf-8")
        )
        member = json.loads(
            (access_root / "doctype/elms_organization_member/elms_organization_member.json").read_text(encoding="utf-8")
        )

        self.assertEqual(organization["name"], "ELMS Organization")
        self.assertEqual(member["name"], "ELMS Organization Member")
        self.assertIn("inn", {field["fieldname"] for field in organization["fields"]})
        self.assertIn("organization", {field["fieldname"] for field in member["fields"]})
        self.assertEqual(ELMS_COMPANY_ADMIN_ROLE, "ELMS Company Admin")
        self.assertEqual(ROLE_PROFILES["ELMS Company Admin Profile"], ("Desk User", ELMS_COMPANY_ADMIN_ROLE))
        self.assertTrue(callable(access_api.create_organization))
        self.assertTrue(callable(access_api.assign_company_admin))

    def test_admin_assignment_creates_membership_and_user_permission(self):
        from elms.access import api as access_api

        class FakeDoc:
            def __init__(self, name: str):
                self.name = name
                self.inserted = False

            def insert(self, **kwargs):
                self.inserted = True
                return self

        user = MagicMock()
        user.roles = []
        user.flags = SimpleNamespace(ignore_permissions=False)
        user.append.side_effect = lambda field, value: user.roles.append(SimpleNamespace(**value))
        records = []

        def fake_get_doc(value, name=None):
            if value == "User":
                return user
            if value == "User" and name:
                return user
            if isinstance(value, dict):
                record = FakeDoc(value["doctype"])
                record.__dict__.update(value)
                records.append(record)
                return record
            raise AssertionError(value)

        def fake_exists(doctype, filters):
            if doctype in {"ELMS Organization", "User"}:
                return True
            return False

        db = MagicMock()
        db.exists.side_effect = fake_exists
        with (
            patch.object(frappe, "session", SimpleNamespace(user="admin@example.com"), create=True),
            patch.object(frappe, "get_roles", return_value=["ELMS Admin"], create=True),
            patch.object(frappe, "db", db, create=True),
            patch.object(frappe, "get_doc", side_effect=fake_get_doc, create=True),
        ):
            result = access_api.assign_company_admin("company@example.com", "Acme")

        self.assertEqual(result["role_profile"], "ELMS Company Admin Profile")
        self.assertEqual(user.role_profile_name, "ELMS Company Admin Profile")
        self.assertIn("ELMS Company Admin", {row.role for row in user.roles})
        self.assertEqual(
            [(record.doctype, record.user, record.organization) for record in records if record.doctype != "User Permission"],
            [("ELMS Organization Member", "company@example.com", "Acme")],
        )
        permission = next(record for record in records if record.doctype == "User Permission")
        self.assertEqual(permission.for_value, "Acme")
        self.assertEqual(permission.allow, "ELMS Organization")

    def test_company_admin_scope_is_server_side_and_fail_closed(self):
        from elms.access import api as access_api

        db = MagicMock()
        db.exists.side_effect = lambda doctype, filters: (
            doctype == "ELMS Organization Member"
            and filters == {"user": "company@example.com", "organization": "Acme"}
        )
        with (
            patch.object(frappe, "session", SimpleNamespace(user="company@example.com"), create=True),
            patch.object(frappe, "get_roles", return_value=["ELMS Company Admin"], create=True),
            patch.object(frappe, "db", db, create=True),
        ):
            self.assertEqual(access_api.require_organization_access("Acme"), "Acme")
            with self.assertRaises(frappe.PermissionError):
                access_api.require_organization_access("Other Org")

    def test_membership_lifecycle_reconciles_user_permission_scope(self):
        from elms.access import api as access_api
        from elms.elms_core.doctype.elms_organization_member.elms_organization_member import (
            ELMSOrganizationMember,
        )

        member = ELMSOrganizationMember()
        member.user = "company@example.com"
        member.organization = "Acme"
        with (
            patch.object(access_api, "_ensure_user_permission") as ensure_scope,
            patch.object(access_api, "_remove_user_permission") as remove_scope,
        ):
            ELMSOrganizationMember.after_insert(member)
            ELMSOrganizationMember.on_update(member)
            ELMSOrganizationMember.after_delete(member)

        ensure_scope.assert_has_calls([
            unittest.mock.call("company@example.com", "Acme"),
            unittest.mock.call("company@example.com", "Acme"),
        ])
        self.assertEqual(ensure_scope.call_count, 2)
        remove_scope.assert_called_once_with("company@example.com", "Acme")

    def test_membership_update_removes_previous_organization_scope(self):
        from elms.access import api as access_api
        from elms.elms_core.doctype.elms_organization_member.elms_organization_member import (
            ELMSOrganizationMember,
        )

        member = ELMSOrganizationMember()
        member.user = "company@example.com"
        member.organization = "Beta"
        member.get_doc_before_save = lambda: SimpleNamespace(
            user="company@example.com", organization="Acme"
        )
        with (
            patch.object(access_api, "_ensure_user_permission") as ensure_scope,
            patch.object(access_api, "_remove_user_permission") as remove_scope,
        ):
            ELMSOrganizationMember.on_update(member)

        ensure_scope.assert_called_once_with("company@example.com", "Beta")
        remove_scope.assert_called_once_with("company@example.com", "Acme")

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
