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


if __name__ == "__main__":
    unittest.main()
