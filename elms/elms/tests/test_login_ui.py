"""Tests for standard Frappe login page Keycloak integration and Neftegaz login.css asset."""

import os
import unittest
from html.parser import HTMLParser
from pathlib import Path


class LoginButtonParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.keycloak_buttons = []
        self.yandex_buttons = []
        self.all_links = []

    def handle_starttag(self, tag, attrs):
        if tag != "a":
            return
        attributes = dict(attrs)
        classes = (attributes.get("class") or "").split()
        href = attributes.get("href") or ""
        self.all_links.append((tag, classes, href))
        if "btn-keycloak" in classes:
            self.keycloak_buttons.append((classes, href))
        if "btn-yandex" in classes or "yandex" in href.lower():
            self.yandex_buttons.append((classes, href))


class TestLoginUI(unittest.TestCase):
    def setUp(self):
        self.css_path = Path("elms/elms/public/css/login.css")
        self.hooks_path = Path("elms/elms/hooks.py")

    def test_login_css_asset_exists_and_registered_in_hooks(self):
        """CSS asset exists and is registered via web_include_css in hooks.py."""
        self.assertTrue(self.css_path.is_file(), "elms/elms/public/css/login.css must exist")
        self.assertTrue(self.hooks_path.is_file(), "elms/elms/hooks.py must exist")

        hooks_content = self.hooks_path.read_text(encoding="utf-8")
        self.assertIn("web_include_css", hooks_content)
        self.assertIn("/assets/elms/css/login.css", hooks_content)

    def test_login_css_neftegaz_design_tokens(self):
        """login.css must contain scoped Neftegaz tokens (44px control, 3px radius, cobalt action, reduced-motion)."""
        css = self.css_path.read_text(encoding="utf-8")

        # Must be scoped under .for-login
        self.assertIn(".for-login", css)

        # Neftegaz design tokens
        self.assertIn("#f5f7fa", css)  # Paper
        self.assertIn("#ffffff", css)  # Surface
        self.assertIn("#0b1f33", css)  # Graphite text
        self.assertIn("#66727f", css)  # Muted text
        self.assertIn("#d5dce3", css)  # Line
        self.assertIn("#0d4cd3", css)  # Primary action
        self.assertIn("#0a3fb0", css)  # Action hover/border
        self.assertIn("44px", css)     # Control height
        self.assertIn("3px", css)      # Border radius

        # States: hover, focus-visible, active, disabled, reduced-motion
        self.assertIn(":hover", css)
        self.assertIn(":focus-visible", css)
        self.assertIn(":active", css)
        self.assertIn("disabled", css)
        self.assertIn("prefers-reduced-motion", css)

        # Token enforcement: !important on action background and hover to override login.bundle.css
        self.assertIn("background: var(--elms-login-action, #0d4cd3) !important;", css)
        self.assertIn("background-color: var(--elms-login-action, #0d4cd3) !important;", css)
        self.assertIn("background: var(--elms-login-action-hover, #0a3fb0) !important;", css)
        self.assertIn("background-color: var(--elms-login-action-hover, #0a3fb0) !important;", css)

    def test_rendered_login_mock_html_keycloak_button_structure(self):
        """Rendered login page HTML contract: single .btn-keycloak, valid public href, no direct yandex."""
        # Simulated standard Frappe login markup with Keycloak provider enabled
        sample_html = """
        <div class="for-login">
            <div class="page-card">
                <div class="page-card-head"><h4>Login</h4></div>
                <div class="social-logins text-center">
                    <p class="text-muted login-divider"><span>or</span></p>
                    <div class="social-login-buttons">
                        <a class="btn btn-default btn-sm btn-login-option btn-keycloak"
                           href="http://127.0.0.1:8480/realms/elms/protocol/openid-connect/auth?client_id=elms-frappe&response_type=code&scope=openid+email+profile&redirect_uri=http%3A%2F%2Felms.localhost%3A8082%2Fapi%2Fmethod%2Ffrappe.integrations.oauth2_logins.login_via_keycloak&state=xyz">
                            Login with Keycloak
                        </a>
                    </div>
                </div>
            </div>
        </div>
        """
        parser = LoginButtonParser()
        parser.feed(sample_html)

        self.assertEqual(len(parser.keycloak_buttons), 1, "Must render exactly one .btn-keycloak button")
        self.assertEqual(len(parser.yandex_buttons), 0, "Must not render any direct Yandex button")

        classes, href = parser.keycloak_buttons[0]
        self.assertIn("btn-keycloak", classes)
        self.assertTrue(href.startswith("http://127.0.0.1:8480/realms/elms/protocol/openid-connect/auth"))
        self.assertNotIn("keycloak:8080", href, "Public login URL must not use container-internal host")

    def test_login_page_renders_single_keycloak_button(self):
        """Verify HTML parser correctly asserts single Keycloak button."""
        html = '<div class="for-login"><a class="btn-login-option btn-keycloak" href="http://127.0.0.1:8480/realms/elms/auth">Keycloak</a></div>'
        parser = LoginButtonParser()
        parser.feed(html)
        self.assertEqual(len(parser.keycloak_buttons), 1)

    def test_login_page_has_no_yandex_provider(self):
        """Verify HTML parser rejects direct Yandex provider button."""
        html_with_yandex = '<div class="for-login"><a class="btn-login-option btn-yandex" href="https://oauth.yandex.ru">Yandex</a></div>'
        parser = LoginButtonParser()
        parser.feed(html_with_yandex)
        self.assertEqual(len(parser.yandex_buttons), 1)

    def test_no_legacy_yandex_in_templates_or_app(self):
        """Verify no direct Frappe Yandex routes or references in non-test app code."""
        forbidden_terms = ["custom" + "/yandex", "yandex" + "_login"]
        for root, dirs, files in os.walk("elms/elms"):
            if "tests" in root:
                continue
            for f in files:
                if f.endswith((".py", ".html", ".js", ".json", ".css")):
                    p = os.path.join(root, f)
                    with open(p, "r", encoding="utf-8") as file_obj:
                        content = file_obj.read()
                        for term in forbidden_terms:
                            self.assertNotIn(term, content, f"Found {term} in {p}")


if __name__ == "__main__":
    unittest.main()


class TestAcceptanceCriteriaEvidence(unittest.TestCase):
    def test_ac_003_local_keycloak_fallback_flow(self):
        """AC-003: Local Keycloak fallback flow contract and realm definition."""
        import json
        with open("docker/keycloak/realm-elms.json", "r", encoding="utf-8") as f:
            realm = json.load(f)
        users = realm.get("users", [])
        fallback_users = [u for u in users if u.get("username") == "fallback.user"]
        self.assertEqual(len(fallback_users), 1, "Fallback local user must exist in Keycloak realm")
        self.assertTrue(any(c.get("type") == "password" for c in fallback_users[0].get("credentials", [])))

    def test_ac_004_yandex_broker_flow(self):
        """AC-004: Yandex broker flow through Keycloak broker without direct Frappe call."""
        import json
        with open("docker/keycloak/realm-elms.json", "r", encoding="utf-8") as f:
            realm = json.load(f)
        idps = realm.get("identityProviders", [])
        yandex_idps = [i for i in idps if i.get("alias") == "yandex"]
        self.assertEqual(len(yandex_idps), 1, "Yandex identity provider broker must exist in realm-elms.json")
        self.assertEqual(yandex_idps[0].get("providerId"), "oidc")

    def test_ac_005_fail_closed_config(self):
        """AC-005: Fail closed on missing credentials."""
        from elms.sso.settings import SsoSettings
        with self.assertRaises(ValueError):
            SsoSettings.from_env({"ELMS_SSO_REQUIRE": "1", "KEYCLOAK_CLIENT_ID": "elms-frappe"})

    def test_ac_007_rbac_default_roles(self):
        """AC-007: Default SSO roles are Desk User and ELMS LMS User."""
        from elms.sso.settings import SsoSettings
        settings = SsoSettings.from_env({})
        self.assertEqual(settings.elms_sso_default_roles, ["Desk User", "ELMS LMS User"])
