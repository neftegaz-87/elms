"""Unit tests for SSO identity mapping between Bitrix emails and Yandex/Keycloak."""

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import frappe
if not hasattr(frappe, "utils"):
    frappe.utils = SimpleNamespace(get_request_session=None)
from elms.sso.mapping import get_mapping_registry, normalize_email
from elms.sso.login import get_sso_authorization_url, authenticate_keycloak


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self.payload = payload
        self.status_code = status_code

    def json(self):
        return self.payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError("upstream error")


class TestSSOIdentityMapping(unittest.TestCase):
    def setUp(self):
        self.registry = get_mapping_registry()

    def test_normalize_email(self):
        self.assertEqual(normalize_email("  AeroAlgo@GMAIL.com "), "aeroalgo@gmail.com")
        self.assertEqual(normalize_email(""), "")
        self.assertEqual(normalize_email(None), "")

    def test_resolve_bitrix_emails_for_required_users(self):
        # Andrey Erokhin
        target_erokhin = self.registry.resolve_target_identity("aeroalgo@gmail.com")
        self.assertEqual(target_erokhin, "erokhin.a@nftgz.ru")
        mapping_erokhin = self.registry.get_mapping("aeroalgo@gmail.com")
        self.assertIsNotNone(mapping_erokhin)
        self.assertEqual(mapping_erokhin.bitrix_id, "274")
        self.assertEqual(mapping_erokhin.full_name, "Ерохин Андрей")
        self.assertEqual(mapping_erokhin.role_profile, "ELMS Admin")
        self.assertIn("ELMS Admin", mapping_erokhin.elms_roles)

        # Evgeny Sokolov
        target_sokolov = self.registry.resolve_target_identity("sokolovavs13@yandex.ru")
        self.assertEqual(target_sokolov, "sokolov.e@nftgz.ru")
        mapping_sokolov = self.registry.get_mapping("sokolovavs13@yandex.ru")
        self.assertIsNotNone(mapping_sokolov)
        self.assertEqual(mapping_sokolov.bitrix_id, "240")
        self.assertIn("ELMS LMS User", mapping_sokolov.elms_roles)

        # Irina Vidyakina
        target_vidyakina = self.registry.resolve_target_identity("ividakina002@gmail.com")
        self.assertEqual(target_vidyakina, "vidyakina.i@nftgz.ru")
        mapping_vidyakina = self.registry.get_mapping("ividakina002@gmail.com")
        self.assertIsNotNone(mapping_vidyakina)
        self.assertEqual(mapping_vidyakina.bitrix_id, "82")
        self.assertIn("ELMS Operations User", mapping_vidyakina.elms_roles)

    def test_resolve_by_login_and_direct_email(self):
        self.assertEqual(self.registry.resolve_target_identity("erokhin.a"), "erokhin.a@nftgz.ru")
        self.assertEqual(self.registry.resolve_target_identity("erokhin.a@nftgz.ru"), "erokhin.a@nftgz.ru")
        self.assertEqual(self.registry.resolve_target_identity("unknown.person@example.com"), "unknown.person@example.com")

    def test_get_sso_authorization_url_resolves_and_attaches_kc_hint(self):
        res = get_sso_authorization_url(user_input="aeroalgo@gmail.com")
        self.assertTrue(res["mapped"])
        self.assertEqual(res["target_identity"], "erokhin.a@nftgz.ru")
        auth_url = res["auth_url"]
        self.assertIn("kc_idp_hint=yandex", auth_url)
        self.assertIn("login_hint=erokhin.a%40nftgz.ru", auth_url)
        self.assertIn("client_id=", auth_url)
        self.assertIn("response_type=code", auth_url)

    def test_authenticate_keycloak_resolves_bitrix_email_transparently(self):
        session = MagicMock()
        session.post.return_value = FakeResponse({"access_token": "token-123"})
        session.get.return_value = FakeResponse({
            "sub": "sub-erokhin-1",
            "email": "erokhin.a@nftgz.ru",
            "preferred_username": "erokhin.a",
            "given_name": "Андрей",
            "family_name": "Ерохин",
        })

        with patch("elms.sso.login.frappe.utils.get_request_session", return_value=session), patch(
            "elms.sso.login._get_keycloak_credentials", return_value=("elms-frappe", "secret")
        ):
            identity = authenticate_keycloak("aeroalgo@gmail.com", "secret-password")

        # Verify that Keycloak was called with the resolved Yandex corporate email, not the Bitrix email
        session.post.assert_called_once()
        call_data = session.post.call_args.kwargs["data"]
        self.assertEqual(call_data["username"], "erokhin.a@nftgz.ru")
        self.assertEqual(identity["email"], "erokhin.a@nftgz.ru")


if __name__ == "__main__":
    unittest.main()
