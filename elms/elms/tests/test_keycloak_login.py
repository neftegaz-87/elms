"""Tests for the server-side Keycloak password flow behind the standard login form."""

import os
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import frappe
if not hasattr(frappe, "utils"):
    frappe.utils = SimpleNamespace(get_request_session=None)
if not hasattr(frappe, "local"):
    frappe.local = SimpleNamespace(flags=SimpleNamespace())
if not hasattr(frappe, "ValidationError"):
    class ValidationError(Exception): pass
    frappe.ValidationError = ValidationError



class FakeResponse:
    def __init__(self, payload, status_code=200):
        self.payload = payload
        self.status_code = status_code

    def json(self):
        return self.payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError("upstream error")


class TestKeycloakLogin(unittest.TestCase):
    def test_invalid_login_uses_validation_error_for_guest_request(self):
        from elms.sso import login

        with patch.object(login.frappe, "throw") as throw:
            login._raise_invalid_login()

        throw.assert_called_once()
        self.assertIs(throw.call_args.args[1], login.frappe.ValidationError)

    def test_server_exchange_uses_internal_keycloak_and_normalizes_identity(self):
        from elms.sso.login import authenticate_keycloak

        session = MagicMock()
        session.post.return_value = FakeResponse({"access_token": "access-token"})
        session.get.return_value = FakeResponse(
            {
                "sub": "kc-sub-1",
                "email": "Test.User@ELMS.LOCAL",
                "email_verified": True,
                "preferred_username": "test.user",
                "given_name": "Test",
                "family_name": "User",
            }
        )

        with patch.dict(
            os.environ,
            {"KEYCLOAK_INTERNAL_URL": "http://keycloak:8080"},
            clear=False,
        ), patch("elms.sso.login.frappe.utils.get_request_session", return_value=session), patch(
            "elms.sso.login._get_keycloak_credentials",
            return_value=("elms-frappe", "client-secret"),
        ):
            identity = authenticate_keycloak("test.user", "password")

        session.post.assert_called_once_with(
            "http://keycloak:8080/realms/elms/protocol/openid-connect/token",
            data={
                "grant_type": "password",
                "client_id": "elms-frappe",
                "client_secret": "client-secret",
                "username": "test.user",
                "password": "password",
                "scope": "openid profile email",
            },
            headers={"Accept": "application/json"},
            timeout=10,
        )
        session.get.assert_called_once_with(
            "http://keycloak:8080/realms/elms/protocol/openid-connect/userinfo",
            headers={"Accept": "application/json", "Authorization": "Bearer access-token"},
            timeout=10,
        )
        self.assertEqual(identity["sub"], "kc-sub-1")
        self.assertEqual(identity["email"], "test.user@elms.local")
        self.assertEqual(identity["first_name"], "Test")
        self.assertEqual(identity["last_name"], "User")

    def test_login_endpoint_provisions_session_through_frappe_oauth_helper(self):
        from elms.sso import login

        login.frappe.response = {"login_token": "one-time-login-token"}
        identity = {
            "sub": "kc-sub-1",
            "email": "test.user@elms.local",
            "email_verified": True,
            "first_name": "Test",
            "last_name": "User",
            "login": "test.user",
        }
        with patch.object(login, "authenticate_keycloak", return_value=identity), patch.object(
            login, "create_oauth_state", return_value="oauth-state"
        ) as create_state, patch.object(login, "login_oauth_user") as login_oauth_user:
            result = login.login_with_keycloak("test.user", "password")

        create_state.assert_called_once_with("/app")
        login_oauth_user.assert_called_once_with(
            identity,
            provider="keycloak",
            state="oauth-state",
            generate_login_token=True,
        )
        self.assertEqual(result, {"login_token": "one-time-login-token"})

    def test_login_oauth_user_runs_with_permissions_ignored_and_restores_flags(self):
        from elms.sso import login

        login.frappe.response = {"login_token": "one-time-login-token"}
        identity = {
            "sub": "kc-sub-1",
            "email": "test.user@elms.local",
            "email_verified": True,
            "first_name": "Test",
            "last_name": "User",
            "login": "test.user",
        }
        observed_flags = []

        def capture_permissions(*args, **kwargs):
            observed_flags.append(getattr(login.frappe.local.flags, "ignore_permissions", None))

        with patch.object(login, "authenticate_keycloak", return_value=identity), patch.object(
            login, "create_oauth_state", return_value="oauth-state"
        ), patch.object(login, "login_oauth_user", side_effect=capture_permissions):
            result = login.login_with_keycloak("test.user", "password")

        self.assertEqual(result, {"login_token": "one-time-login-token"})
        self.assertEqual(observed_flags, [True])
        self.assertIsNone(getattr(login.frappe.local.flags, "ignore_permissions", None))


if __name__ == "__main__":
    unittest.main()
