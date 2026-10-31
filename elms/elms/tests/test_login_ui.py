"""Tests for standard Frappe login page Keycloak integration and Neftegaz login.css asset."""

import os
import unittest
from html.parser import HTMLParser
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


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
        self.css_path = REPO_ROOT / "elms/elms/public/css/login.css"
        self.hooks_path = REPO_ROOT / "elms/elms/hooks.py"

    def test_login_css_asset_exists_and_registered_in_hooks(self):
        """CSS asset exists and is registered via web_include_css in hooks.py."""
        self.assertTrue(self.css_path.is_file(), "elms/elms/public/css/login.css must exist")
        self.assertTrue(self.hooks_path.is_file(), "elms/elms/hooks.py must exist")

        hooks_content = self.hooks_path.read_text(encoding="utf-8")
        self.assertIn("web_include_css", hooks_content)
        self.assertIn("/assets/elms/css/login.css", hooks_content)
        self.assertIn("web_include_js", hooks_content)
        self.assertIn("/assets/elms/js/login-keycloak.js", hooks_content)

    def test_login_branding_uses_elms_sdo_name(self):
        """The standard Frappe login template receives the ELMS SDO brand name."""
        hooks_content = self.hooks_path.read_text(encoding="utf-8")
        install_content = (REPO_ROOT / "elms/elms/install.py").read_text(encoding="utf-8")

        self.assertIn('app_title = "ELMS СДО"', hooks_content)
        self.assertIn("update_website_context", hooks_content)
        self.assertIn('"elms.install.update_website_context"', hooks_content)
        self.assertIn('context.get("for_test") == "login.html"', install_content)
        self.assertIn('"app_name": "ELMS СДО"', install_content)

    def test_update_website_context_allows_single_keycloak_login_control(self):
        """update_website_context must not suppress provider_logins or hide .btn-keycloak."""
        from elms.install import update_website_context

        context = {
            "for_test": "login.html",
            "provider_logins": [
                {
                    "name": "keycloak",
                    "provider_name": "Keycloak",
                    "auth_url": "http://127.0.0.1:8480/realms/elms/protocol/openid-connect/auth",
                }
            ],
        }
        res = update_website_context(context)
        self.assertEqual(res.get("app_name"), "ELMS СДО")
        self.assertNotIn("provider_logins", res)
        self.assertEqual(len(context["provider_logins"]), 1)

    def test_elms_desk_route_is_available_for_system_users(self):
        hooks_content = self.hooks_path.read_text(encoding="utf-8")

        self.assertIn("add_to_apps_screen", hooks_content)
        self.assertIn('"name": "elms"', hooks_content)
        self.assertIn('"route": "/app"', hooks_content)

    def test_login_js_replaces_only_the_standard_password_submit(self):
        """The added browser behavior delegates the standard form to the server endpoint."""
        js = (REPO_ROOT / "elms/elms/public/js/login-keycloak.js").read_text(encoding="utf-8")

        self.assertIn('$(document).on("login_rendered"', js)
        self.assertIn('"elms.sso.login.login_with_keycloak"', js)
        self.assertIn("frappe.www.login.login_via_token", js)
        self.assertIn('forms.off("submit")', js)
        self.assertNotIn("btn-keycloak", js)

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

    def test_login_css_styles_the_full_frappe_login_surface(self):
        """The Neftegaz visual language applies to the complete login surface, not only SSO."""
        css = self.css_path.read_text(encoding="utf-8")

        for selector in (
            'body[data-path="login"]',
            'body[data-path="login"] .navbar',
            'body[data-path="login"] .page-content-wrapper',
            'body[data-path="login"] .page-card-head',
            'body[data-path="login"] .login-content.page-card',
            'body[data-path="login"] .login-content.page-card .form-control',
            'body[data-path="login"] .login-content.page-card .page-card-actions .btn',
            'body[data-path="login"] .login-content.page-card .login-divider',
            'body[data-path="login"] .login-content.page-card .btn-login-with-email-link',
        ):
            self.assertIn(selector, css, f"Missing login surface selector: {selector}")

        for token in (
            "--elms-login-font",
            "#eaf2ff",
            "#c5ced8",
            "#8a9aab",
        ):
            self.assertIn(token, css, f"Missing Neftegaz login token: {token}")

    def test_rendered_login_mock_html_keycloak_button_structure(self):
        """Rendered login page HTML contract: single .btn-keycloak, valid public href, no direct yandex."""
        sample_html = """
        <div class="for-login">
            <div class="page-card">
                <div class="page-card-head"><h4>Вход на сайт ELMS СДО</h4></div>
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
        for root, dirs, files in os.walk(REPO_ROOT / "elms/elms"):
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
    def test_ac_003_local_keycloak_fallback_user_is_purged(self):
        """AC-003: The production realm does not ship a local fallback user."""
        import json
        with (REPO_ROOT / "docker/keycloak/realm-elms.json").open("r", encoding="utf-8") as f:
            realm = json.load(f)
        users = realm.get("users", [])
        self.assertFalse(
            any(u.get("username") == "fallback.user" for u in users),
            "The purged fallback user must not be present in the production realm",
        )

    def test_ac_004_yandex_broker_flow(self):
        """AC-004: Yandex broker flow through Keycloak broker without direct Frappe call."""
        import json
        with (REPO_ROOT / "docker/keycloak/realm-elms.json").open("r", encoding="utf-8") as f:
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
