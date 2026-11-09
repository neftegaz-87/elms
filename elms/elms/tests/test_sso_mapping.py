"""Unit tests for SSO identity mapping between Bitrix emails and Yandex/Keycloak."""

import unittest
import os
from types import SimpleNamespace
from unittest.mock import patch

import frappe
if not hasattr(frappe, "utils"):
    frappe.utils = SimpleNamespace(get_request_session=None)
from elms.sso.mapping import get_mapping_registry, normalize_email
from elms.sso.login import get_sso_authorization_url


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
        self.assertEqual(mapping_erokhin.role_profile, "ELMS Admin Profile")
        self.assertIn("ELMS Admin", mapping_erokhin.elms_roles)

        # Evgeny Sokolov
        target_sokolov = self.registry.resolve_target_identity("sokolovavs13@yandex.ru")
        self.assertEqual(target_sokolov, "sokolov.e@nftgz.ru")
        mapping_sokolov = self.registry.get_mapping("sokolovavs13@yandex.ru")
        self.assertIsNotNone(mapping_sokolov)
        self.assertEqual(mapping_sokolov.bitrix_id, "240")
        self.assertIn("ELMS Learner", mapping_sokolov.elms_roles)

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

    def test_authorization_callback_is_absolute(self):
        res = get_sso_authorization_url(user_input="erokhin.a@nftgz.ru")
        self.assertIn(
            "redirect_uri=http%3A%2F%2Felms.localhost%3A8082%2Fapi%2Fmethod%2Ffrappe.integrations.oauth2_logins.login_via_keycloak",
            res["auth_url"],
        )

    def test_local_keycloak_authorization_has_no_yandex_hint_in_explicit_dev_mode(self):
        with patch.dict(os.environ, {"ELMS_ALLOW_LOCAL_KEYCLOAK_LOGIN": "1"}):
            res = get_sso_authorization_url(
                user_input="elms.test.one@elms.local",
                mode="local",
            )

        self.assertNotIn("kc_idp_hint=", res["auth_url"])
        self.assertIn("login_hint=elms.test.one%40elms.local", res["auth_url"])


    def test_password_mode_authorization_has_no_yandex_hint(self):
        res = get_sso_authorization_url(
            user_input="elms.test.admin@elms.local",
            mode="password",
        )
        self.assertNotIn("kc_idp_hint=", res["auth_url"])
        self.assertIn("login_hint=elms.test.admin%40elms.local", res["auth_url"])

    def test_unsupported_mode_raises_error(self):
        with self.assertRaises(Exception):
            get_sso_authorization_url(user_input="test@test.ru", mode="invalid_mode")


if __name__ == "__main__":
    unittest.main()
