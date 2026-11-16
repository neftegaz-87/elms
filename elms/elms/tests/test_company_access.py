"""Contracts for the company-scoped role and access management surface."""

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import frappe

from elms.access import api as access_api


class TestCompanyAccessContract(unittest.TestCase):
    def test_company_context_exposes_only_internal_profiles(self):
        with (
            patch.object(access_api, "_is_admin", return_value=False),
            patch.object(access_api, "_roles", return_value={"ELMS Company Admin"}),
            patch.object(access_api, "_organizations_for_user", return_value=["Acme"]),
        ):
            result = access_api.get_company_access_context()

        self.assertEqual(result["organization"], "Acme")
        self.assertEqual(
            result["profiles"],
            [
                "ELMS Learner Profile",
                "ELMS Instructor Profile",
                "ELMS Methodologist Profile",
                "ELMS Company Admin Profile",
            ],
        )
        self.assertFalse(result["platform_admin"])

    def test_company_admin_cannot_assign_platform_profile(self):
        with (
            patch.object(access_api, "_is_admin", return_value=False),
            patch.object(access_api, "_roles", return_value={"ELMS Company Admin"}),
            patch.object(access_api, "require_organization_access", return_value="Acme"),
        ):
            with self.assertRaises(frappe.PermissionError):
                access_api.update_organization_member(
                    user="person@example.com",
                    organization="Acme",
                    role_profile="ELMS Admin Profile",
                )

    def test_company_admin_can_change_internal_profile_and_roles(self):
        user = MagicMock()
        user.name = "person@example.com"
        user.roles = [
            SimpleNamespace(role="Desk User"),
            SimpleNamespace(role="ELMS Learner"),
        ]
        user.set.side_effect = lambda field, rows: setattr(
            user, field, [SimpleNamespace(**row) for row in rows]
        )
        user.flags = SimpleNamespace(ignore_permissions=False)
        member = MagicMock()
        member.name = "member-1"
        member.user = user.name
        member.organization = "Acme"
        member.role_profile = "ELMS Learner Profile"

        with (
            patch.object(access_api, "_is_admin", return_value=False),
            patch.object(access_api, "_roles", return_value={"ELMS Company Admin"}),
            patch.object(access_api, "require_organization_access", return_value="Acme"),
            patch.object(access_api, "_get_member", return_value=member),
            patch.object(frappe, "get_doc", return_value=user, create=True),
        ):
            result = access_api.update_organization_member(
                user="person@example.com",
                organization="Acme",
                role_profile="ELMS Instructor Profile",
            )

        self.assertEqual(result["role_profile"], "ELMS Instructor Profile")
        self.assertEqual(member.role_profile, "ELMS Instructor Profile")
        self.assertEqual(
            {row.role for row in user.roles},
            {"Desk User", "ELMS Instructor"},
        )
        user.save.assert_called_once()
        member.save.assert_called_once()

    def test_company_admin_can_disable_only_member_in_scope(self):
        user = MagicMock()
        user.name = "person@example.com"
        user.enabled = 1
        member = SimpleNamespace(name="member-1", user=user.name, organization="Acme")

        with (
            patch.object(access_api, "_is_admin", return_value=False),
            patch.object(access_api, "_roles", return_value={"ELMS Company Admin"}),
            patch.object(access_api, "require_organization_access", return_value="Acme"),
            patch.object(access_api, "_get_member", return_value=member),
            patch.object(frappe, "get_doc", return_value=user, create=True),
        ):
            result = access_api.disable_organization_member("person@example.com", "Acme")

        self.assertEqual(result["user"], "person@example.com")
        self.assertEqual(user.enabled, 0)
        user.save.assert_called_once()


if __name__ == "__main__":
    unittest.main()
