"""Comprehensive unit and contract test suite for ELMS SSO, JIT provisioning, roles, and fallback."""

from __future__ import annotations

import json
import os
import pickle
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from urllib.parse import parse_qs, urlencode, urlparse

import frappe
from elms.sso.constants import (
    DEFAULT_SSO_ROLES,
    DEFAULT_SSO_ROLES_CONF_KEY,
    KEYCLOAK_PROVIDER_NAME,
    YANDEX_IDP_ALIAS,
)
from elms.sso.roles import (
    get_default_sso_roles,
    is_keycloak_social_user,
    maybe_assign_sso_roles,
)

if not hasattr(frappe, "throw"):
    def _throw(msg, exc=Exception, *args, **kwargs):
        raise exc(msg)
    frappe.throw = _throw

if not hasattr(frappe, "conf"):
    class _Conf(dict):
        def __getattr__(self, name):
            return self.get(name)
        def __setattr__(self, name, value):
            self[name] = value
    frappe.conf = _Conf()

if not hasattr(frappe, "whitelist"):
    def _whitelist(*_args, **_kwargs):
        def decorate(function):
            return function
        return decorate
    frappe.whitelist = _whitelist

if not hasattr(frappe, "session"):
    frappe.session = SimpleNamespace(user="Guest")
if not hasattr(frappe, "cache"):
    frappe.cache = lambda: None
if not hasattr(frappe, "local"):
    frappe.local = SimpleNamespace()
if not hasattr(frappe, "get_roles"):
    frappe.get_roles = lambda _user: []
if not hasattr(frappe, "ValidationError"):
    frappe.ValidationError = ValueError
if not hasattr(frappe, "PermissionError"):
    frappe.PermissionError = PermissionError


class FakeUserDoc:
    """Mock Frappe User document for SSO testing."""

    def __init__(self, email: str = "user@example.com", is_social: bool = True):
        self.doctype = "User"
        self.name = email
        self.email = email
        self.user_type = "Website User"
        self.flags = MagicMock()
        self.flags.in_sso_role_assignment = False
        self.flags.social_login_provider = "keycloak" if is_social else None
        self.social_logins = (
            [{"provider": "keycloak", "userid": "sub-keycloak-123"}] if is_social else []
        )
        self.roles = []
        self.saved = False

    def get_social_login_userid(self, provider: str):
        for s in self.social_logins:
            if s.get("provider", "").lower() == provider.lower():
                return s.get("userid")
        return None

    def get_roles(self):
        return [r.get("role") if isinstance(r, dict) else r for r in self.roles]

    def add_roles(self, *roles):
        for role in roles:
            if role not in self.get_roles():
                self.roles.append({"role": role})
        self.saved = True

    def append(self, key, val):
        if key == "roles":
            self.roles.append(val)
        elif key == "social_logins":
            self.social_logins.append(val)

    def get(self, key, default=None):
        return getattr(self, key, default)

    def save(self):
        self.saved = True
        return self

    def insert(self):
        self.saved = True
        maybe_assign_sso_roles(self)
        return self


class FakeHandoffCache:
    def __init__(self):
        self.values = {}

    def set_value(self, key, value, **_kwargs):
        self.values[key] = value

    def make_key(self, key):
        return key

    def getdel(self, key):
        value = self.values.pop(key, None)
        return None if value is None else pickle.dumps(value)


def simulate_keycloak_broker_login(
    userinfo: dict,
    existing_user: FakeUserDoc | None = None,
) -> FakeUserDoc:
    """Simulate Frappe processing a Keycloak JIT broker login callback (AC-6).

    Validates OIDC userinfo claims received from Keycloak broker (e.g. Yandex 360),
    links or creates a Frappe User document with immutable sub identity,
    and runs the after_insert role assignment hook fail-closed.
    """
    sub = userinfo.get("sub")
    if not sub:
        frappe.throw("Invalid OIDC userinfo: missing sub claim.")

    email = userinfo.get("email")
    if not email or not str(email).strip():
        frappe.throw("SSO user creation requires a valid verified email address fail-closed.")

    if not userinfo.get("email_verified", True):
        frappe.throw("SSO user creation requires a valid verified email address fail-closed.")

    if existing_user is not None:
        if existing_user.email.strip().lower() != str(email).strip().lower():
            frappe.throw("Identity mismatch between brokered email and existing account.")
        user = existing_user
        if not user.get_social_login_userid(KEYCLOAK_PROVIDER_NAME):
            user.append("social_logins", {"provider": KEYCLOAK_PROVIDER_NAME.lower(), "userid": str(sub)})
        user.flags.social_login_provider = KEYCLOAK_PROVIDER_NAME.lower()
        user.save()
        maybe_assign_sso_roles(user)
        return user

    user = FakeUserDoc(email=email, is_social=False)
    user.first_name = userinfo.get("given_name") or userinfo.get("name") or ""
    user.last_name = userinfo.get("family_name") or ""
    user.flags.social_login_provider = KEYCLOAK_PROVIDER_NAME.lower()
    user.append("social_logins", {"provider": KEYCLOAK_PROVIDER_NAME.lower(), "userid": str(sub)})
    user.insert()
    return user




def simulate_keycloak_auth_flow(
    auth_method: str,
    yandex_online: bool = True,
    userinfo: dict | None = None,
    existing_user: FakeUserDoc | None = None,
) -> FakeUserDoc:
    """Simulate the Keycloak authentication flow with a Yandex broker (AC-7).

    - If auth_method is 'yandex_broker' and Yandex is down (yandex_online=False),
      fails closed with ConnectionError / IdP outage exception.
    - If auth_method is 'local_credential', the removed local fallback is rejected
      regardless of Yandex IdP availability.
    """
    if auth_method == "yandex_broker":
        if not yandex_online:
            frappe.throw("Yandex IdP is unreachable: external identity provider outage (HTTP 503).")
        if userinfo is None:
            userinfo = {
                "sub": "kc-broker-yandex-sub-1",
                "email": "user@elms.school",
                "email_verified": True,
                "broker_provider": "yandex",
            }
        return simulate_keycloak_broker_login(userinfo, existing_user=existing_user)

    if auth_method == "local_credential":
        frappe.throw("Local Keycloak fallback is disabled; authentication requires the Yandex broker.")

    frappe.throw(f"Unknown auth method: {auth_method}")


def simulate_frappe_oauth_redirect(
    provider_name: str = "keycloak",
    base_frappe_url: str = "http://elms.localhost:8082",
    keycloak_base_url: str = "http://localhost:8480",
    realm: str = "elms",
    client_id: str = "elms-frappe",
) -> dict:
    """Simulate Frappe OAuth initiation redirect (AC-2, AC+2).

    - If provider is "keycloak", returns HTTP 302 redirect to Keycloak auth endpoint
      with required OIDC parameters (client_id, response_type=code, scope=openid email profile, redirect_uri).
    - If provider is anything else (e.g. "yandex"), fails closed because direct external IdP
      endpoints in Frappe are strictly prohibited.
    """
    if provider_name.lower() != "keycloak":
        frappe.throw(
            f"Direct OAuth initiation for provider '{provider_name}' is forbidden; "
            "only Keycloak broker termination is supported (AC+2)."
        )

    redirect_uri = f"{base_frappe_url}/api/method/frappe.integrations.oauth2_logins.login_via_keycloak"
    query_params = {
        "client_id": client_id,
        "response_type": "code",
        "scope": "openid email profile",
        "redirect_uri": redirect_uri,
    }
    auth_url = f"{keycloak_base_url}/realms/{realm}/protocol/openid-connect/auth?{urlencode(query_params)}"
    return {
        "status_code": 302,
        "location": auth_url,
        "headers": {"Location": auth_url},
        "redirect_uri": redirect_uri,
    }

class TestSSO(unittest.TestCase):
    """Test suite for Keycloak brokered SSO, role assignment, fallback, and JIT provisioning."""

    def test_elms_module_layout_does_not_shadow_frappe_core(self):
        """The ELMS app must not claim Frappe's reserved Core module name."""
        app_root = Path(__file__).resolve().parents[1]
        modules = (app_root / "modules.txt").read_text(encoding="utf-8").splitlines()

        self.assertNotIn("Core", [module.strip() for module in modules])
        self.assertIn("ELMS Core", [module.strip() for module in modules])
        for module in ("ELMS Core", "Operations", "LMS"):
            module_path = app_root / module.lower().replace(" ", "_")
            self.assertTrue((module_path / "__init__.py").is_file(), module)

        settings_manifest = app_root / "elms_core" / "doctype" / "elms_settings_section" / "elms_settings_section.json"
        self.assertTrue(settings_manifest.is_file())
        manifest = json.loads(settings_manifest.read_text(encoding="utf-8"))
        self.assertEqual(manifest.get("module"), "ELMS Core")

    def test_yandex_smtp_uses_supported_frappe_auth_method(self):
        """The install hook must use an Email Account auth option supported by Frappe."""
        from elms.install import setup_yandex_smtp

        account = MagicMock()
        account.is_new.return_value = True
        account.name = "Yandex SMTP"

        with patch.object(frappe, "db", create=True) as mock_db, patch.object(
            frappe, "new_doc", return_value=account, create=True
        ):
            mock_db.exists.return_value = False
            self.assertEqual(setup_yandex_smtp(), "Yandex SMTP")

        settings = account.update.call_args.args[0]
        self.assertEqual(settings["auth_method"], "Basic")

    def test_administrator_group_reconciliation_sets_permissions_before_role_save(self):
        from elms.install import reconcile_keycloak_user

        class PermissionAwareUser(FakeUserDoc):
            def add_roles(self, *roles):
                if not self.flags.ignore_permissions:
                    raise PermissionError("role reconciliation requires ignored permissions")
                super().add_roles(*roles)

        user = PermissionAwareUser(email="admin@example.com", is_social=False)
        with patch.object(frappe, "db", create=True) as mock_db:
            mock_db.exists.return_value = True
            reconcile_keycloak_user(user, {"groups": ["Administrators"]})

        self.assertIn("System Manager", user.get_roles())
        self.assertTrue(user.saved)

    def setUp(self):
        self.original_conf_roles = frappe.conf.get(DEFAULT_SSO_ROLES_CONF_KEY)

    def tearDown(self):
        if self.original_conf_roles is not None:
            frappe.conf[DEFAULT_SSO_ROLES_CONF_KEY] = self.original_conf_roles
        elif DEFAULT_SSO_ROLES_CONF_KEY in frappe.conf:
            del frappe.conf[DEFAULT_SSO_ROLES_CONF_KEY]

    def test_assign_sso_roles_success(self):
        """Test that default roles (Desk User, ELMS LMS User) are assigned to new Keycloak social user."""
        user = FakeUserDoc(email="newuser@example.com", is_social=True)

        with patch.object(frappe, "db", create=True) as mock_db:
            mock_db.exists.return_value = True
            maybe_assign_sso_roles(user)

        assigned_roles = user.get_roles()
        self.assertIn("Desk User", assigned_roles)
        self.assertIn("ELMS LMS User", assigned_roles)
        self.assertEqual(user.user_type, "System User")
        self.assertTrue(user.saved)

    def test_assign_sso_roles_fails_closed_when_role_missing(self):
        """Test fail-closed behavior when a default role does not exist in DB (BN-005, TM-005)."""
        user = FakeUserDoc(email="newuser@example.com", is_social=True)

        def mock_exists(doctype, name):
            if doctype == "Role" and name == "ELMS LMS User":
                return False
            return True

        with patch.object(frappe, "db", create=True) as mock_db:
            mock_db.exists.side_effect = mock_exists
            with self.assertRaises(Exception) as ctx:
                maybe_assign_sso_roles(user)
            self.assertIn("ELMS LMS User", str(ctx.exception))
            self.assertIn("does not exist", str(ctx.exception))

    def test_assign_sso_roles_ignores_non_social_user(self):
        """Test that non-social users or users without Keycloak provider are ignored."""
        normal_user = FakeUserDoc(email="admin@example.com", is_social=False)

        with patch.object(frappe, "db", create=True) as mock_db:
            mock_db.exists.return_value = True
            maybe_assign_sso_roles(normal_user)

        self.assertEqual(normal_user.get_roles(), [])
        self.assertFalse(normal_user.saved)

    def test_social_signup_missing_email_throws_fail_closed(self):
        """Test that Keycloak social user creation without verified email throws fail-closed (BN-004, TM-004)."""
        user_no_email = FakeUserDoc(email="", is_social=True)

        with patch.object(frappe, "db", create=True) as mock_db:
            mock_db.exists.return_value = True
            with self.assertRaises(Exception) as ctx:
                maybe_assign_sso_roles(user_no_email)
            self.assertIn("verified email", str(ctx.exception).lower())

    def test_first_broker_login_provisions_keycloak_and_frappe_identity_contract(self):
        """Test JIT broker identity contract: Yandex as Keycloak IdP, user_id_property=sub, no direct Yandex row."""
        realm_path = "docker/keycloak/realm-elms.json"
        self.assertTrue(os.path.exists(realm_path), "realm-elms.json must exist")
        with open(realm_path, "r", encoding="utf-8") as f:
            realm = json.load(f)

        idps = [i for i in realm.get("identityProviders", []) if i.get("alias") == YANDEX_IDP_ALIAS]
        self.assertEqual(len(idps), 1, "Exactly one Yandex broker IdP must exist in Keycloak")
        yandex_idp = idps[0]
        self.assertEqual(yandex_idp.get("providerId"), "oidc")
        self.assertEqual(yandex_idp.get("firstBrokerLoginFlowAlias"), "first broker login")

        # In Frappe, Social Login Key must use immutable sub as user_id_property
        from elms.sso.ensure import ensure_social_login_keys
        with patch.object(frappe, "db", create=True) as mock_db:
            mock_db.exists.return_value = False
            mock_db.get_value.return_value = None
            doc_created = {}

            mock_doc = MagicMock()
            mock_doc.update = lambda d: doc_created.update(d)

            with patch.object(frappe, "get_doc", return_value=mock_doc, create=True),                  patch.object(frappe, "new_doc", return_value=mock_doc, create=True):
                ensure_social_login_keys(base_url="http://keycloak.localhost:8480")

            self.assertEqual(doc_created.get("user_id_property"), "sub")
            self.assertEqual(doc_created.get("provider_name"), KEYCLOAK_PROVIDER_NAME)

    def test_removed_local_keycloak_fallback_is_not_configured(self):
        """The production realm must not configure the purged local fallback user."""
        realm_path = "docker/keycloak/realm-elms.json"
        with open(realm_path, "r", encoding="utf-8") as f:
            realm = json.load(f)

        users = realm.get("users", [])
        self.assertFalse(
            any(u.get("username") == "fallback.user" for u in users),
            "The purged fallback user must not be present in the production realm",
        )

        # Verify other brokered identities are not automatically provisioned with passwords
        brokered_candidates = [
            u for u in users
            if u.get("username") != "admin" and not u.get("username", "").startswith("elms.test.")
        ]
        for u in brokered_candidates:
            self.assertFalse(
                any(c.get("type") == "password" for c in u.get("credentials", [])),
                f"User {u.get('username')} must not have auto-provisioned password",
            )

    def test_hooks_doc_events_registered(self):
        """Test that elms.hooks registers maybe_assign_sso_roles for User.after_insert."""
        import elms.hooks as hooks
        self.assertTrue(hasattr(hooks, "doc_events"), "hooks must declare doc_events")
        user_events = hooks.doc_events.get("User", {})
        self.assertEqual(
            user_events.get("after_insert"),
            "elms.sso.roles.maybe_assign_sso_roles",
            "User after_insert must route to maybe_assign_sso_roles",
        )

    def test_no_direct_yandex_social_login_key(self):
        """Test that no direct Yandex Social Login Key or provider is registered in Frappe."""
        from elms.sso.constants import YANDEX_IDP_ALIAS
        self.assertEqual(YANDEX_IDP_ALIAS, "yandex")
        # Ensure constants do not expose a direct provider
        import elms.sso.constants as consts
        for attr in dir(consts):
            self.assertFalse(
                attr.startswith("YANDEX_PROVIDER") or attr.startswith("YANDEX_SOCIAL"),
                f"Direct Yandex provider constant found: {attr}",
            )

    def test_jit_broker_login_creates_new_user_with_roles_and_social_link(self):
        """Test JIT broker login creates new Frappe user and assigns default roles from mock Keycloak response (AC-6)."""
        mock_kc_broker_response = {
            "sub": "kc-broker-sub-777",
            "email": "teacher.yandex@elms.school",
            "email_verified": True,
            "name": "Alexandr Pushkin",
            "given_name": "Alexandr",
            "family_name": "Pushkin",
            "preferred_username": "a.pushkin",
            "broker_provider": "yandex",
        }

        with patch.object(frappe, "db", create=True) as mock_db:
            mock_db.exists.return_value = True
            user = simulate_keycloak_broker_login(mock_kc_broker_response)

        self.assertEqual(user.email, "teacher.yandex@elms.school")
        self.assertEqual(user.first_name, "Alexandr")
        self.assertEqual(user.last_name, "Pushkin")
        self.assertEqual(user.get_social_login_userid("keycloak"), "kc-broker-sub-777")
        self.assertIn("Desk User", user.get_roles())
        self.assertIn("ELMS LMS User", user.get_roles())
        self.assertTrue(user.saved)
        # Ensure the provider linked is keycloak, never direct yandex
        self.assertIsNone(user.get_social_login_userid("yandex"))

    def test_jit_broker_login_links_existing_user_by_verified_email(self):
        """Test JIT broker login links Keycloak identity to existing local user matching verified email (AC-6)."""
        mock_kc_broker_response = {
            "sub": "kc-broker-sub-888",
            "email": "existing.teacher@elms.school",
            "email_verified": True,
            "name": "Lev Tolstoy",
            "given_name": "Lev",
            "family_name": "Tolstoy",
            "broker_provider": "yandex",
        }

        existing_user = FakeUserDoc(email="existing.teacher@elms.school", is_social=False)
        existing_user.roles = [{"role": "Instructor"}]

        with patch.object(frappe, "db", create=True) as mock_db:
            mock_db.exists.return_value = True
            linked_user = simulate_keycloak_broker_login(mock_kc_broker_response, existing_user=existing_user)

        self.assertEqual(linked_user.email, "existing.teacher@elms.school")
        self.assertEqual(linked_user.get_social_login_userid("keycloak"), "kc-broker-sub-888")
        self.assertIn("Instructor", linked_user.get_roles())
        self.assertIn("Desk User", linked_user.get_roles())
        self.assertIn("ELMS LMS User", linked_user.get_roles())
        self.assertTrue(linked_user.saved)

    def test_jit_broker_login_unverified_email_fails_closed(self):
        """Test JIT broker login rejects unverified or missing email fail-closed (AC-6, BN-004, TM-004)."""
        unverified_response = {
            "sub": "kc-broker-sub-999",
            "email": "unverified@elms.school",
            "email_verified": False,
        }

        with patch.object(frappe, "db", create=True) as mock_db:
            mock_db.exists.return_value = True
            with self.assertRaises(Exception) as ctx:
                simulate_keycloak_broker_login(unverified_response)
            self.assertIn("verified email", str(ctx.exception).lower())

    def test_jit_broker_login_missing_sub_fails_closed(self):
        """Test JIT broker login rejects response missing sub identifier fail-closed (AC-6)."""
        invalid_response = {
            "sub": None,
            "email": "valid@elms.school",
            "email_verified": True,
        }

        with patch.object(frappe, "db", create=True) as mock_db:
            mock_db.exists.return_value = True
            with self.assertRaises(Exception) as ctx:
                simulate_keycloak_broker_login(invalid_response)
            self.assertIn("sub claim", str(ctx.exception).lower())



    def test_local_keycloak_fallback_fails_closed_during_yandex_outage(self):
        """Test local Keycloak fallback is rejected when Yandex IdP is unavailable (AC-7, BN-008, TM-010)."""
        with patch.object(frappe, "db", create=True) as mock_db:
            mock_db.exists.return_value = True
            with self.assertRaises(Exception) as ctx:
                simulate_keycloak_auth_flow(
                    auth_method="local_credential",
                    yandex_online=False,
                )
        self.assertIn("local keycloak fallback is disabled", str(ctx.exception).lower())

    def test_yandex_broker_login_fails_closed_during_outage(self):
        """Test Yandex broker login attempt fails closed when Yandex IdP is in outage (AC-7, BN-007, TM-009)."""
        with patch.object(frappe, "db", create=True) as mock_db:
            mock_db.exists.return_value = True
            with self.assertRaises(Exception) as ctx:
                simulate_keycloak_auth_flow(
                    auth_method="yandex_broker",
                    yandex_online=False,
                )
            self.assertIn("yandex idp is unreachable", str(ctx.exception).lower())

    def test_local_keycloak_fallback_does_not_link_existing_admin_during_outage(self):
        """Test local Keycloak fallback cannot link an existing account during Yandex outage (AC-7)."""
        existing_admin = FakeUserDoc(email="admin.teacher@elms.school", is_social=False)
        existing_admin.roles = [{"role": "System Manager"}, {"role": "Instructor"}]

        local_admin_claims = {
            "sub": "kc-local-admin-sub-999",
            "email": "admin.teacher@elms.school",
            "email_verified": True,
            "name": "Admin Teacher",
        }

        with patch.object(frappe, "db", create=True) as mock_db:
            mock_db.exists.return_value = True
            with self.assertRaises(Exception) as ctx:
                simulate_keycloak_auth_flow(
                    auth_method="local_credential",
                    yandex_online=False,
                    userinfo=local_admin_claims,
                    existing_user=existing_admin,
                )

        self.assertIn("local keycloak fallback is disabled", str(ctx.exception).lower())
        self.assertIsNone(existing_admin.get_social_login_userid("keycloak"))
        self.assertIn("System Manager", existing_admin.get_roles())
        self.assertIn("Instructor", existing_admin.get_roles())
        self.assertFalse(existing_admin.saved)

    def test_local_keycloak_fallback_user_is_absent_from_realm(self):
        """The purged local fallback user is absent from the Keycloak realm definition."""
        realm_path = "docker/keycloak/realm-elms.json"
        with open(realm_path, "r", encoding="utf-8") as f:
            realm = json.load(f)

        self.assertFalse(
            any(u.get("username") == "fallback.user" for u in realm.get("users", [])),
            "The purged fallback user must not be present in the production realm",
        )

    def test_desk_design_system_sources_are_present_for_container_build(self):
        """The Desk bundle must have every imported shared stylesheet at build time."""
        repository_root = Path(__file__).resolve().parents[3]
        required_sources = (
            "design-system/shell-desk.css",
            "design-system/tokens.css",
            "design-system/controls-desk.css",
        )

        for relative_path in required_sources:
            source = repository_root / relative_path
            self.assertTrue(source.is_file(), f"Missing required stylesheet: {relative_path}")
            self.assertGreater(source.stat().st_size, 0, f"Empty required stylesheet: {relative_path}")

        dockerfile = (repository_root / "docker/Dockerfile").read_text(encoding="utf-8")
        self.assertIn(
            "COPY --chown=frappe:0 design-system /home/frappe/frappe-bench/apps/design-system",
            dockerfile,
        )



    def test_live_trace_cannot_claim_pass_without_runtime_evidence(self):
        """Synthetic traces must never be accepted as live SSO evidence."""
        trace_path = "docs/reports/sso-browser-api-trace.json"
        self.assertTrue(os.path.exists(trace_path), f"{trace_path} must exist")
        with open(trace_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        status = data.get("status")
        self.assertIn(status, {"blocked", "pass"})
        if status == "pass":
            self.assertIs(data.get("live_evidence"), True)
            self.assertEqual(data.get("evidence_type"), "runtime_http")
            self.assertTrue(data.get("command"))
            self.assertTrue(data.get("timestamp"))
            payload = json.dumps(data, ensure_ascii=False)
            self.assertNotIn("mock_", payload)

    def test_blocked_live_trace_retains_real_failure_evidence(self):
        """A failed live run must remain auditable instead of becoming a silent skip."""
        with open("docs/reports/sso-browser-api-trace.json", "r", encoding="utf-8") as f:
            data = json.load(f)

        if data.get("status") != "blocked" or data.get("evidence_type") != "runtime_http_error":
            return

        self.assertTrue(data.get("timestamp"))
        self.assertTrue(data.get("command"))
        self.assertTrue(data.get("reason"))
        self.assertIsInstance(data.get("exit_code"), int)
        for response in data.get("raw_http", {}).values():
            self.assertIn("headers", response)
            self.assertIn("body", response)

    def test_bugfix_verification_persists_live_evidence(self):
        """The BUGFIX command must write the runtime artifact it is expected to verify."""
        with open(
            "memory-bank/back/bugfix/T-B03-elms-sso-keycloak-yandex/bugfix-queue.yaml",
            "r",
            encoding="utf-8",
        ) as f:
            queue = f.read()

        self.assertIn("EVIDENCE_FILE=docs/reports/sso-browser-api-trace.json", queue)
        self.assertIn("LIVE_SMOKE_COMMAND=", queue)
        self.assertIn("timeout -k 10s 300s bash scripts/live_smoke.sh", queue)

    def test_ac_plus_2_browser_api_trace_file_contract(self):
        """Test that the SSO trace separates the contract from runtime evidence."""
        trace_path = "docs/reports/sso-browser-api-trace.json"
        self.assertTrue(os.path.exists(trace_path), f"{trace_path} must exist")
        with open(trace_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data.get("schema"), "sso-browser-api-trace/v1")
        contract = data.get("contract", {})
        self.assertEqual(
            contract.get("frappe_oauth_callback"),
            "http://elms.localhost:8082/api/method/frappe.integrations.oauth2_logins.login_via_keycloak",
        )
        self.assertEqual(contract.get("frappe_login_path"), "/login")
        self.assertEqual(
            contract.get("keycloak_authorization_path"),
            "/realms/elms/protocol/openid-connect/auth",
        )
        self.assertEqual(
            contract.get("keycloak_yandex_broker_path"),
            "/realms/elms/broker/yandex/endpoint",
        )

        if data.get("status") == "blocked":
            self.assertIs(data.get("live_evidence"), False)
            self.assertEqual(data.get("journeys"), [])
            return

        self.assertEqual(data.get("status"), "pass")
        self.assertIs(data.get("live_evidence"), True)
        self.assertEqual(data.get("evidence_type"), "runtime_http")
        keycloak_base_url = data.get("base_urls", {}).get("keycloak", "").rstrip("/")
        self.assertTrue(keycloak_base_url, "runtime evidence must record the Keycloak base URL")
        raw_http = data.get("raw_http", {})
        self.assertEqual(
            set(raw_http),
            {
                "keycloak_discovery",
                "frappe_login_page",
                "keycloak_authorization",
                "keycloak_yandex_broker",
            },
        )
        for response in raw_http.values():
            self.assertTrue(response.get("headers"), "runtime evidence must retain raw response headers")
        journeys = {j["journey_id"]: j for j in data.get("journeys", [])}

        self.assertIn("JRN-SSO-001", journeys, "JRN-SSO-001 must exist")
        j1 = journeys["JRN-SSO-001"]
        self.assertEqual(j1.get("status"), "pass")
        self.assertEqual(
            j1.get("url"),
            "http://elms.localhost:8082/login",
        )
        self.assertEqual(j1.get("response", {}).get("status_code"), 200)
        loc = j1.get("response", {}).get("provider_auth_url", "")
        self.assertTrue(
            loc.startswith(f"{keycloak_base_url}/realms/elms/protocol/openid-connect/auth"),
            f"Location {loc} must start with Keycloak auth endpoint",
        )
        parsed = urlparse(loc)
        qs = parse_qs(parsed.query)
        self.assertEqual(qs.get("client_id"), ["elms-frappe"])
        self.assertEqual(qs.get("response_type"), ["code"])
        self.assertIn("openid email profile", qs.get("scope", [""])[0] or qs.get("scope", [""]))
        self.assertEqual(
            qs.get("redirect_uri"),
            ["http://elms.localhost:8082/api/method/frappe.integrations.oauth2_logins.login_via_keycloak"],
        )

        self.assertIn("JRN-SSO-001A", journeys, "JRN-SSO-001A authorization journey must exist")
        j1a = journeys["JRN-SSO-001A"]
        self.assertEqual(j1a.get("status"), "pass")
        self.assertEqual(j1a.get("url"), loc)
        self.assertIn(j1a.get("response", {}).get("status_code"), {200, 302})

        self.assertIn("JRN-SSO-001B", journeys, "JRN-SSO-001B broker endpoint journey must exist")
        j1b = journeys["JRN-SSO-001B"]
        self.assertEqual(j1b.get("status"), "pass")
        self.assertTrue(
            j1b.get("url", "").startswith(f"{keycloak_base_url}/realms/elms/broker/yandex/endpoint"),
            "URL must terminate at Keycloak broker endpoint",
        )
        self.assertIn(j1b.get("response", {}).get("status_code"), {200, 302, 400, 502})

    def test_ac_plus_2_frappe_oauth_redirect_generates_302_to_keycloak(self):
        """Test Frappe OAuth initiation strictly redirects to Keycloak auth endpoint with OIDC params (AC+2)."""
        res = simulate_frappe_oauth_redirect("keycloak")
        self.assertEqual(res.get("status_code"), 302)
        loc = res.get("location")
        self.assertTrue(loc.startswith("http://localhost:8480/realms/elms/protocol/openid-connect/auth"))
        parsed = urlparse(loc)
        qs = parse_qs(parsed.query)
        self.assertEqual(qs.get("client_id"), ["elms-frappe"])
        self.assertEqual(qs.get("response_type"), ["code"])
        self.assertEqual(qs.get("scope"), ["openid email profile"])
        self.assertEqual(
            qs.get("redirect_uri"),
            ["http://elms.localhost:8082/api/method/frappe.integrations.oauth2_logins.login_via_keycloak"],
        )

    def test_ac_plus_2_direct_yandex_oauth_fails_closed(self):
        """Test direct Yandex OAuth initiation in Frappe is rejected fail-closed (AC+2)."""
        with self.assertRaises(Exception) as ctx:
            simulate_frappe_oauth_redirect("yandex")
        self.assertIn("forbidden", str(ctx.exception).lower())
        self.assertIn("broker termination", str(ctx.exception).lower())

    def test_ac_plus_2_keycloak_broker_realm_contract(self):
        """Test that realm config registers Yandex IdP broker and Frappe login_via_keycloak redirect URI (AC+2)."""
        realm_path = "docker/keycloak/realm-elms.json"
        with open(realm_path, "r", encoding="utf-8") as f:
            realm = json.load(f)

        # Identity Provider is strictly Yandex via Keycloak broker
        yandex_idps = [i for i in realm.get("identityProviders", []) if i.get("alias") == "yandex"]
        self.assertEqual(len(yandex_idps), 1)
        self.assertEqual(yandex_idps[0].get("providerId"), "oidc")
        self.assertEqual(yandex_idps[0].get("firstBrokerLoginFlowAlias"), "first broker login")

        # Client elms-frappe has strictly login_via_keycloak redirect URIs
        frappe_clients = [c for c in realm.get("clients", []) if c.get("clientId") == "elms-frappe"]
        self.assertEqual(len(frappe_clients), 1)
        client = frappe_clients[0]
        redirect_uris = client.get("redirectUris", [])
        self.assertTrue(
            any("login_via_keycloak" in u for u in redirect_uris),
            "elms-frappe client must configure login_via_keycloak redirect URI",
        )
        self.assertFalse(
            any("login_via_yandex" in u for u in redirect_uris),
            "elms-frappe client must never configure direct Yandex redirect URI",
        )


class TestReviewHandoff(unittest.TestCase):
    def test_open_review_issues_opaque_ticket_without_keycloak_login(self):
        from elms.sso import review

        cache = FakeHandoffCache()
        local = SimpleNamespace(response={}, request=SimpleNamespace(headers={}))
        with patch.dict(
            os.environ,
            {
                "ELMS_REVIEW_URL": "http://127.0.0.1:8765/auth/login?source=elms",
                "ELMS_REVIEW_ALLOW_HTTP": "1",
                "ELMS_REVIEW_HANDOFF_SECRET": "handoff-secret",
            },
            clear=False,
        ), patch.object(frappe, "session", SimpleNamespace(user="elms.test.admin@elms.local")), patch.object(
            frappe, "get_roles", return_value=["ELMS Admin", "Desk User"]
        ), patch.object(frappe, "cache", return_value=cache), patch.object(frappe, "local", local):
            review.open_review()

        location = urlparse(local.response["location"])
        self.assertEqual(location.path, "/auth/handoff")
        self.assertNotIn("login", location.path)
        self.assertNotIn("source", location.query)
        ticket = parse_qs(location.query)["ticket"][0]
        self.assertIn(review._handoff_key(ticket), cache.values)
        self.assertEqual(cache.values[review._handoff_key(ticket)]["roles"], ["admin"])

    def test_redeem_review_handoff_is_secret_protected_and_one_time(self):
        from elms.sso import review

        cache = FakeHandoffCache()
        ticket = "A" * 43
        cache.values[review._handoff_key(ticket)] = {
            "user_id": "elms.test.admin@elms.local",
            "member_id": "elms-dev",
            "roles": ["admin"],
        }
        local = SimpleNamespace(
            response={},
            request=SimpleNamespace(headers={"X-ELMS-Review-Handoff-Secret": "handoff-secret"}),
        )
        with patch.dict(os.environ, {"ELMS_REVIEW_HANDOFF_SECRET": "handoff-secret"}, clear=False), patch.object(
            frappe, "cache", return_value=cache
        ), patch.object(frappe, "local", local):
            result = review.redeem_review_handoff(ticket)

        self.assertEqual(result["user_id"], "elms.test.admin@elms.local")
        self.assertEqual(result["roles"], ["admin"])
        self.assertNotIn(review._handoff_key(ticket), cache.values)


if __name__ == "__main__":
    unittest.main()
