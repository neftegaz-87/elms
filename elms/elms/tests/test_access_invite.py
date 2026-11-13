"""Contract tests for the ELMS-to-Keycloak invite operation."""

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import frappe

from elms.access import api as access_api
from elms.access.keycloak import KeycloakProvisionError


class TestInviteContract(unittest.TestCase):
    def test_learner_membership_cannot_invite(self):
        with (
            patch.object(access_api, "_is_admin", return_value=False),
            patch.object(access_api, "_roles", return_value={"ELMS Learner"}),
            patch.object(access_api, "_db_exists", return_value=True),
        ):
            with self.assertRaises(frappe.PermissionError):
                access_api.invite_org_user("person@example.com", "Person", "User", "Acme")

    def test_invite_returns_keycloak_identity_without_password(self):
        with (
            patch.object(access_api, "_is_admin", return_value=True),
            patch.object(access_api, "_db_exists", return_value=False),
            patch.object(access_api, "_create_or_get_frappe_user", return_value=(SimpleNamespace(name="person@example.com", flags=SimpleNamespace()), True)),
            patch.object(access_api, "_ensure_membership_and_scope"),
            patch.object(access_api, "_get_keycloak_client") as client_factory,
        ):
            client = client_factory.return_value
            client.upsert_user.return_value = "kc-1"
            result = access_api.invite_org_user("person@example.com", "Person", "User", "Acme")

        self.assertEqual(result["keycloak_id"], "kc-1")
        self.assertTrue(result["invited"])
        self.assertNotIn("password", result)
        client.send_password_setup.assert_called_once_with("kc-1")

    def test_keycloak_failure_disables_new_local_user_and_raises(self):
        user = SimpleNamespace(name="person@example.com", enabled=1, flags=SimpleNamespace(), save=MagicMock())
        with (
            patch.object(access_api, "_is_admin", return_value=True),
            patch.object(access_api, "_db_exists", return_value=False),
            patch.object(access_api, "_create_or_get_frappe_user", return_value=(user, True)),
            patch.object(access_api, "_ensure_membership_and_scope"),
            patch.object(access_api, "_get_keycloak_client") as client_factory,
        ):
            client_factory.return_value.upsert_user.side_effect = KeycloakProvisionError("provider unavailable")
            with self.assertRaises(KeycloakProvisionError):
                access_api.invite_org_user("person@example.com", "Person", "User", "Acme")

        self.assertEqual(user.enabled, 0)
        user.save.assert_called_once()


if __name__ == "__main__":
    unittest.main()
