import json
import os
import re
import tempfile
import unittest
from urllib.parse import urlparse

FORBIDDEN_IDP_KEY = "_".join(["yandex", "login"])


class TestSSOConfiguration(unittest.TestCase):
    def test_sso_constants_defined(self):
        """Test that canonical SSO constants are defined and exported correctly."""
        from elms.sso.constants import (
            DEFAULT_SSO_ROLES,
            DEFAULT_SSO_ROLES_CONF_KEY,
            KEYCLOAK_LOGIN_CONF_KEY,
            KEYCLOAK_PROVIDER_NAME,
            YANDEX_IDP_ALIAS,
        )

        self.assertEqual(KEYCLOAK_PROVIDER_NAME, "Keycloak")
        self.assertEqual(YANDEX_IDP_ALIAS, "yandex")
        self.assertEqual(KEYCLOAK_LOGIN_CONF_KEY, "keycloak_login")
        self.assertEqual(DEFAULT_SSO_ROLES, ("Desk User", "ELMS LMS User"))
        self.assertEqual(DEFAULT_SSO_ROLES_CONF_KEY, "elms_sso_default_roles")

        # Explicitly verify no direct external IdP provider constants exist
        import elms.sso.constants as consts
        self.assertFalse(hasattr(consts, "YANDEX" + "_LOGIN_CONF_KEY"))
        self.assertFalse(hasattr(consts, "YANDEX" + "_PROVIDER_NAME"))

    def test_realm_elms_client_structure(self):
        """Test that docker/keycloak/realm-elms.json defines confidential elms-frappe client with exact callback."""
        realm_path = "docker/keycloak/realm-elms.json"
        self.assertTrue(os.path.exists(realm_path), f"{realm_path} does not exist")
        with open(realm_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data.get("realm"), "elms")
        self.assertFalse(data.get("registrationAllowed", True))

        clients = data.get("clients", [])
        frappe_clients = [c for c in clients if c.get("clientId") == "elms-frappe"]
        self.assertEqual(len(frappe_clients), 1, "elms-frappe client must exist in realm-elms.json")
        client = frappe_clients[0]

        self.assertFalse(client.get("publicClient"), "elms-frappe must be confidential (publicClient=False)")
        self.assertTrue(client.get("standardFlowEnabled"))
        self.assertEqual(client.get("protocol"), "openid-connect")

        redirect_uris = client.get("redirectUris", [])
        callback_uri = "http://elms.localhost:8082/api/method/frappe.integrations.oauth2_logins.login_via_keycloak"
        self.assertIn(callback_uri, redirect_uris, "redirectUris must contain login_via_keycloak callback")

        review_clients = [c for c in clients if c.get("clientId") == "neftegaz-review"]
        self.assertEqual(len(review_clients), 1, "neftegaz-review client must exist in realm-elms.json")
        review = review_clients[0]
        self.assertFalse(review.get("publicClient"))
        self.assertTrue(review.get("standardFlowEnabled"))
        self.assertEqual(review.get("secret"), "${env.NEFTEGAZ_REVIEW_CLIENT_SECRET:}")
        self.assertEqual(review.get("redirectUris"), ["__NEFTEGAZ_REVIEW_PUBLIC_URL__/auth/callback"])
        self.assertEqual(
            {mapper.get("name") for mapper in review.get("protocolMappers", [])},
            {"review-roles", "bitrix-user-id", "bitrix-member-id", "bitrix-department-ids"},
        )

        review_roles = data.get("roles", {}).get("client", {}).get("neftegaz-review", [])
        self.assertEqual(
            {role.get("name") for role in review_roles},
            {"review_admin", "review_dispatcher", "review_queue_supervisor"},
        )

    def test_keycloak_client_urls_are_valid_import_values(self):
        """Keycloak must be able to import every client URL without shell placeholders or invalid wildcards."""
        with open("docker/keycloak/realm-elms.json", "r", encoding="utf-8") as f:
            client = next(c for c in json.load(f)["clients"] if c.get("clientId") == "elms-frappe")

        for field in ("rootUrl", "baseUrl"):
            value = client.get(field, "")
            parsed = urlparse(value)
            self.assertTrue(parsed.scheme and parsed.netloc, f"{field} must be an absolute URL")
            self.assertNotIn("${", value, f"{field} must not contain an unresolved placeholder")

        redirect_uris = client.get("redirectUris", [])
        self.assertNotIn("/*", redirect_uris, "a hostless wildcard is not a valid Keycloak redirect URI")
        for uri in redirect_uris:
            parsed = urlparse(uri.replace("/*", "/placeholder"))
            self.assertTrue(parsed.scheme and parsed.netloc, f"Invalid redirect URI: {uri}")

    def test_keycloak_yandex_broker_structure(self):
        """Test that Keycloak realm configures Yandex only as an OIDC broker with first-broker-login."""
        realm_path = "docker/keycloak/realm-elms.json"
        with open(realm_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        idps = data.get("identityProviders", [])
        yandex_idps = [i for i in idps if i.get("alias") == "yandex"]
        self.assertEqual(len(yandex_idps), 1, "Yandex identity provider must exist in realm-elms.json")
        yandex = yandex_idps[0]

        self.assertEqual(yandex.get("providerId"), "oidc")
        self.assertEqual(yandex.get("firstBrokerLoginFlowAlias"), "first broker login")
        self.assertTrue(yandex.get("trustEmail"))
        self.assertTrue(yandex.get("enabled"))

    def test_dev_test_users_use_environment_backed_passwords(self):
        """The local verification accounts must be Keycloak-only and never carry passwords in git."""
        with open("docker/keycloak/realm-elms.json", "r", encoding="utf-8") as f:
            users = json.load(f).get("users", [])

        expected = {
            "elms.test.one@elms.local": ("KEYCLOAK_TEST_ONE_PASSWORD", "employee", "/Employees"),
            "elms.test.two@elms.local": ("KEYCLOAK_TEST_TWO_PASSWORD", "employee", "/Employees"),
            "elms.test.admin@elms.local": ("KEYCLOAK_TEST_ADMIN_PASSWORD", "admin", "/Administrators"),
        }
        users_by_username = {user.get("username"): user for user in users}
        for username, (env_name, role, group) in expected.items():
            self.assertIn(username, users_by_username)
            user = users_by_username[username]
            self.assertEqual(user.get("email"), username)
            self.assertTrue(user.get("emailVerified"))
            self.assertIn(role, user.get("realmRoles", []))
            self.assertIn(group, user.get("groups", []))
            credentials = user.get("credentials", [])
            self.assertEqual(len(credentials), 1)
            self.assertEqual(credentials[0].get("type"), "password")
            self.assertEqual(credentials[0].get("value"), f"${{env.{env_name}}}")

        with open("docker/compose.dev.yaml", encoding="utf-8") as f:
            compose = f.read()
        for env_name, _, _ in expected.values():
            self.assertIn(f"{env_name}: ${{{env_name}:-}}", compose)

    def test_site_config_injection_structure(self):
        """Test site_config generation and injection from environment variables without direct IdP login."""
        import elms.sso.conf as sso_conf

        self.assertTrue(hasattr(sso_conf, "inject_sso_site_config"))

        # Case 1: Full credentials provided in env -> generates keycloak_login and roles
        test_env = {
            "KEYCLOAK_CLIENT_ID": "test-keycloak-id",
            "KEYCLOAK_CLIENT_SECRET": "test-keycloak-secret",
            "YANDEX_CLIENT_ID": "test-yandex-id",
            "YANDEX_CLIENT_SECRET": "test-yandex-secret",
            "ELMS_SSO_DEFAULT_ROLES": "Custom Role, Desk User",
        }
        cfg = sso_conf.build_sso_site_config(test_env)
        self.assertEqual(cfg["keycloak_login"], {"client_id": "test-keycloak-id", "client_secret": "test-keycloak-secret"})
        self.assertNotIn(FORBIDDEN_IDP_KEY, cfg)
        self.assertEqual(cfg["elms_sso_default_roles"], ["Custom Role", "Desk User"])

        # Case 2: Missing secrets keeps provider keys omitted (BN-001)
        empty_env = {}
        cfg_empty = sso_conf.build_sso_site_config(empty_env)
        self.assertNotIn("keycloak_login", cfg_empty)
        self.assertNotIn(FORBIDDEN_IDP_KEY, cfg_empty)
        self.assertEqual(cfg_empty["elms_sso_default_roles"], ["Desk User", "ELMS LMS User"])

        # Case 3: ELMS_SSO_REQUIRE=1 with missing secrets throws ValueError
        req_env = {"ELMS_SSO_REQUIRE": "1"}
        with self.assertRaises(ValueError):
            sso_conf.build_sso_site_config(req_env)

        # Case 4: inject_sso_site_config writes into site_config.json file and purges any legacy IdP key
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".json") as tmp:
            tmp.write(json.dumps({"developer_mode": 1, FORBIDDEN_IDP_KEY: {"client_id": "bad"}}))
            tmp_path = tmp.name

        try:
            res = sso_conf.inject_sso_site_config(site_config_path=tmp_path, env=test_env)
            with open(tmp_path, "r", encoding="utf-8") as f:
                saved = json.load(f)
            self.assertEqual(saved.get("developer_mode"), 1)
            self.assertEqual(saved.get("keycloak_login"), {"client_id": "test-keycloak-id", "client_secret": "test-keycloak-secret"})
            self.assertNotIn(FORBIDDEN_IDP_KEY, saved)
            self.assertEqual(saved.get("elms_sso_default_roles"), ["Custom Role", "Desk User"])
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_no_secrets_in_tracked_files(self):
        """Test that zero real client secrets or passwords with long entropy are committed in tracked files."""
        secret_pattern = re.compile(r'(client_secret|password)\s*[:=]\s*["\']([0-9a-zA-Z]{16,})["\']', re.IGNORECASE)
        scanned_paths = [
            "docker/keycloak/realm-elms.json",
            ".env.example",
            "docker/.env.dev.example",
            "docker/compose.dev.yaml",
            "elms/elms/sso/constants.py",
            "elms/elms/sso/conf.py",
        ]
        for p in scanned_paths:
            if not os.path.exists(p):
                continue
            with open(p, "r", encoding="utf-8") as f:
                content = f.read()
            matches = secret_pattern.findall(content)
            self.assertEqual(len(matches), 0, f"Found possible hardcoded secrets in {p}: {matches}")


if __name__ == "__main__":
    unittest.main()


class TestSsoSettingsContract(unittest.TestCase):
    def test_sso_settings_validates_all_seven_contract_variables(self):
        """FR-004: Validate all 7 contract env variables with typed SsoSettings adapter."""
        from elms.sso.settings import SsoSettings

        env = {
            "KEYCLOAK_CLIENT_ID": "elms-frappe",
            "KEYCLOAK_CLIENT_SECRET": "secret123",
            "KEYCLOAK_PUBLIC_URL": "http://127.0.0.1:8480",
            "YANDEX_CLIENT_ID": "yandex-id",
            "YANDEX_CLIENT_SECRET": "yandex-secret",
            "ELMS_SSO_DEFAULT_ROLES": "Desk User, ELMS LMS User",
            "ELMS_SSO_REQUIRE": "1",
        }
        settings = SsoSettings.from_env(env)
        self.assertEqual(settings.keycloak_client_id, "elms-frappe")
        self.assertEqual(settings.keycloak_client_secret.get_secret_value(), "secret123")
        self.assertEqual(settings.keycloak_public_url, "http://127.0.0.1:8480")
        self.assertEqual(settings.yandex_client_id, "yandex-id")
        self.assertEqual(settings.yandex_client_secret.get_secret_value(), "yandex-secret")
        self.assertEqual(settings.elms_sso_default_roles, ["Desk User", "ELMS LMS User"])
        self.assertTrue(settings.elms_sso_require)

    def test_sso_settings_fail_closed_on_missing_secret_when_required(self):
        """ELMS_SSO_REQUIRE=1 with missing client secret must raise ValueError (fail-closed)."""
        from elms.sso.settings import SsoSettings

        env = {
            "KEYCLOAK_CLIENT_ID": "elms-frappe",
            "KEYCLOAK_PUBLIC_URL": "http://127.0.0.1:8480",
            "ELMS_SSO_REQUIRE": "1",
        }
        with self.assertRaises(ValueError):
            SsoSettings.from_env(env)

    def test_public_url_never_contains_container_hostname(self):
        """KEYCLOAK_PUBLIC_URL with keycloak:8080 must be rejected."""
        from elms.sso.settings import SsoSettings

        with self.assertRaises(ValueError):
            SsoSettings(
                keycloak_client_id="elms-frappe",
                keycloak_client_secret="sec",
                keycloak_public_url="http://keycloak:8080",
            )

    def test_keycloak_entrypoint_credential_branches(self):
        """Test entrypoint Yandex credential branch logic using shell simulation."""
        import subprocess

        # Branch 1: both empty -> exit 0 (disables broker)
        res1 = subprocess.run(
            ["sh", "docker/keycloak/entrypoint.sh", "--dry-run"],
            env={**os.environ, "YANDEX_CLIENT_ID": "", "YANDEX_CLIENT_SECRET": ""},
            capture_output=True,
            text=True,
        )
        self.assertEqual(res1.returncode, 0, f"Both empty should succeed: {res1.stderr}")

        # Branch 2: partial (ID only) -> exit 1
        res2 = subprocess.run(
            ["sh", "docker/keycloak/entrypoint.sh", "--dry-run"],
            env={**os.environ, "YANDEX_CLIENT_ID": "some-id", "YANDEX_CLIENT_SECRET": ""},
            capture_output=True,
            text=True,
        )
        self.assertEqual(res2.returncode, 1, "Partial credentials must exit non-zero")

        # Branch 3: partial (SECRET only) -> exit 1
        res3 = subprocess.run(
            ["sh", "docker/keycloak/entrypoint.sh", "--dry-run"],
            env={**os.environ, "YANDEX_CLIENT_ID": "", "YANDEX_CLIENT_SECRET": "some-sec"},
            capture_output=True,
            text=True,
        )
        self.assertEqual(res3.returncode, 1, "Partial credentials must exit non-zero")

        # Branch 4: both present -> exit 0 (enables broker)
        res4 = subprocess.run(
            ["sh", "docker/keycloak/entrypoint.sh", "--dry-run"],
            env={**os.environ, "YANDEX_CLIENT_ID": "some-id", "YANDEX_CLIENT_SECRET": "some-sec"},
            capture_output=True,
            text=True,
        )
        self.assertEqual(res4.returncode, 0, f"Both present should succeed: {res4.stderr}")

        partial_test_users = subprocess.run(
            ["sh", "docker/keycloak/entrypoint.sh", "--dry-run"],
            env={
                **os.environ,
                "KEYCLOAK_TEST_ONE_PASSWORD": "one-password",
                "KEYCLOAK_TEST_TWO_PASSWORD": "",
                "KEYCLOAK_TEST_ADMIN_PASSWORD": "",
            },
            capture_output=True,
            text=True,
        )
        self.assertEqual(partial_test_users.returncode, 1)
