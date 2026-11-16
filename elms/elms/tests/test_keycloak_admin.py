"""Contract tests for the server-only Keycloak Admin client."""

import unittest
from unittest.mock import MagicMock, patch

from elms.access.keycloak import (
    KeycloakAdminClient,
    KeycloakAdminSettings,
    KeycloakConfigError,
    KeycloakProvisionError,
)


class Response:
    def __init__(self, status_code=200, payload=None, headers=None):
        self.status_code = status_code
        self._payload = payload or {}
        self.headers = headers or {}
        self.text = str(self._payload)

    def json(self):
        return self._payload


class TestKeycloakAdminClient(unittest.TestCase):
    def test_missing_admin_secret_fails_closed(self):
        with self.assertRaises(KeycloakConfigError):
            KeycloakAdminSettings.from_env({"KEYCLOAK_ADMIN_BASE_URL": "http://keycloak:8080", "KEYCLOAK_ADMIN_REALM": "elms"})

    def test_empty_environment_does_not_fall_back_to_process_environment(self):
        with self.assertRaises(KeycloakConfigError):
            KeycloakAdminSettings.from_env({})

    def test_upsert_existing_user_and_send_password_action(self):
        session = MagicMock()
        session.post.return_value = Response(payload={"access_token": "token"})
        session.request.side_effect = [
            Response(payload=[{"id": "kc-1", "email": "person@example.com"}]),
            Response(),
            Response(),
        ]
        client = KeycloakAdminClient(
            KeycloakAdminSettings.from_env(
                {
                    "KEYCLOAK_ADMIN_BASE_URL": "http://keycloak:8080",
                    "KEYCLOAK_ADMIN_REALM": "elms",
                    "KEYCLOAK_ADMIN_CLIENT_ID": "elms-admin",
                    "KEYCLOAK_ADMIN_CLIENT_SECRET": "super-secret",
                }
            ),
            session=session,
        )

        user_id = client.upsert_user("person@example.com", "Person", "User")
        client.send_password_setup("kc-1")

        self.assertEqual(user_id, "kc-1")
        action_call = session.request.call_args_list[-1]
        self.assertIn("execute-actions-email", action_call.args[1])
        self.assertEqual(action_call.kwargs["json"], ["UPDATE_PASSWORD"])
        self.assertNotIn("super-secret", repr(action_call))

    def test_provider_failure_is_typed_and_secret_safe(self):
        session = MagicMock()
        session.post.return_value = Response(status_code=401, payload={"error": "invalid_client"})
        client = KeycloakAdminClient(
            KeycloakAdminSettings.from_env(
                {
                    "KEYCLOAK_ADMIN_BASE_URL": "http://keycloak:8080",
                    "KEYCLOAK_ADMIN_REALM": "elms",
                    "KEYCLOAK_ADMIN_CLIENT_ID": "elms-admin",
                    "KEYCLOAK_ADMIN_CLIENT_SECRET": "super-secret",
                }
            ),
            session=session,
        )

        with self.assertRaises(KeycloakProvisionError) as raised:
            client.upsert_user("person@example.com", "Person", "User")
        self.assertNotIn("super-secret", str(raised.exception))

    def test_upsert_marks_user_for_elms_first_login_password_surface(self):
        session = MagicMock()
        session.post.return_value = Response(payload={"access_token": "token"})
        empty_search = Response()
        empty_search._payload = []
        session.request.side_effect = [empty_search, Response(headers={"Location": "/users/kc-1"})]
        client = KeycloakAdminClient(
            KeycloakAdminSettings.from_env(
                {
                    "KEYCLOAK_ADMIN_BASE_URL": "http://keycloak:8080",
                    "KEYCLOAK_ADMIN_REALM": "elms",
                    "KEYCLOAK_ADMIN_CLIENT_ID": "elms-admin",
                    "KEYCLOAK_ADMIN_CLIENT_SECRET": "super-secret",
                }
            ),
            session=session,
        )

        client.upsert_user("person@example.com", "Person", "User")

        payload = session.request.call_args_list[-1].kwargs["json"]
        self.assertEqual(payload["attributes"], {"elms_first_login_password_change": ["true"]})

    def test_set_password_and_update_required_actions_use_keycloak_admin_api(self):
        session = MagicMock()
        session.post.return_value = Response(payload={"access_token": "token"})
        session.request.side_effect = [Response(), Response(), Response()]
        client = KeycloakAdminClient(
            KeycloakAdminSettings.from_env(
                {
                    "KEYCLOAK_ADMIN_BASE_URL": "http://keycloak:8080",
                    "KEYCLOAK_ADMIN_REALM": "elms",
                    "KEYCLOAK_ADMIN_CLIENT_ID": "elms-admin",
                    "KEYCLOAK_ADMIN_CLIENT_SECRET": "super-secret",
                }
            ),
            session=session,
        )

        client.set_password("kc/1", "new-password")
        client.update_required_actions("kc/1", ["CONFIGURE_TOTP"])
        client.update_attributes("kc/1", {"source": ["invite"]})

        password_call = session.request.call_args_list[0]
        self.assertEqual(password_call.args[0], "PUT")
        self.assertIn("users/kc%2F1/reset-password", password_call.args[1])
        self.assertEqual(password_call.kwargs["json"], {"type": "password", "value": "new-password", "temporary": False})
        action_call = session.request.call_args_list[1]
        self.assertEqual(action_call.kwargs["json"], {"requiredActions": ["CONFIGURE_TOTP"]})
        attributes_call = session.request.call_args_list[2]
        self.assertEqual(attributes_call.kwargs["json"], {"attributes": {"source": ["invite"]}})


if __name__ == "__main__":
    unittest.main()
