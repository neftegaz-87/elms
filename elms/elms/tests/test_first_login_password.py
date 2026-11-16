"""Tests for the ELMS first-login Keycloak password boundary."""

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import frappe


class TestFirstLoginPassword(unittest.TestCase):
    def setUp(self):
        frappe.session = SimpleNamespace(user="person@example.com")

    def test_state_reads_keycloak_required_action(self):
        from elms.sso import password

        client = MagicMock()
        client.find_user.return_value = {
            "id": "kc-1",
            "requiredActions": [],
            "attributes": {"elms_first_login_password_change": ["true"]},
        }
        with patch.object(password, "_keycloak_client", return_value=client):
            self.assertEqual(password.get_password_change_state(), {"required": True})

        client.find_user.assert_called_once_with("person@example.com")

    def test_change_password_updates_keycloak_and_preserves_other_actions(self):
        from elms.sso import password

        client = MagicMock()
        client.find_user.return_value = {
            "id": "kc-1",
            "requiredActions": ["UPDATE_PASSWORD", "CONFIGURE_TOTP"],
            "attributes": {"elms_first_login_password_change": ["true"], "source": ["invite"]},
        }
        with patch.object(password, "_keycloak_client", return_value=client):
            result = password.change_password("new-secure-password", "new-secure-password")

        self.assertEqual(result, {"changed": True, "required": False})
        client.set_password.assert_called_once_with("kc-1", "new-secure-password")
        client.update_required_actions.assert_called_once_with("kc-1", ["CONFIGURE_TOTP"])
        client.update_attributes.assert_called_once_with("kc-1", {"source": ["invite"]})

    def test_change_password_rejects_mismatch_before_keycloak_call(self):
        from elms.sso import password

        client = MagicMock()
        with patch.object(password, "_keycloak_client", return_value=client), self.assertRaises(Exception):
            password.change_password("new-secure-password", "different-password")

        client.find_user.assert_not_called()


if __name__ == "__main__":
    unittest.main()
