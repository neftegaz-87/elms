"""Unit tests for idempotent Keycloak-only Social Login Key ensure module."""

import json
import unittest
from unittest.mock import MagicMock, patch

import frappe
from elms.sso.constants import (
    DEFAULT_KEYCLOAK_CLIENT_ID,
    DEFAULT_KEYCLOAK_REALM,
    KEYCLOAK_DEFAULT_REDIRECT_URL,
    KEYCLOAK_LOGIN_CONF_KEY,
    KEYCLOAK_PROVIDER_NAME,
    YANDEX_IDP_ALIAS,
)

if not hasattr(frappe, "scrub"):
    def scrub(text: str) -> str:
        return text.replace(" ", "_").replace("-", "_").lower()
    frappe.scrub = scrub

if not hasattr(frappe, "throw"):
    frappe.throw = lambda msg, *args, **kwargs: (_ for _ in ()).throw(Exception(msg))

if not hasattr(frappe, "conf"):
    class Conf(dict):
        def __getattr__(self, name):
            return self.get(name)
        def __setattr__(self, name, value):
            self[name] = value
    frappe.conf = Conf()


class FakeSocialLoginDoc:
    """In-memory mock for Frappe Document representing Social Login Key."""

    def __init__(self, name: str, is_new: bool = True):
        self.name = name
        self._is_new = is_new
        self.flags = MagicMock()
        self.provider_name = ""
        self.social_login_provider = ""
        self.custom_base_url = 0
        self.base_url = ""
        self.authorize_url = ""
        self.access_token_url = ""
        self.redirect_url = ""
        self.api_endpoint = ""
        self.auth_url_data = ""
        self.user_id_property = ""
        self.sign_ups = ""
        self.client_id = None
        self.client_secret = None
        self.enable_social_login = 0

    def is_new(self) -> bool:
        return self._is_new

    def update(self, values: dict) -> None:
        for k, v in values.items():
            setattr(self, k, v)

    def insert(self) -> "FakeSocialLoginDoc":
        self._is_new = False
        return self

    def save(self) -> "FakeSocialLoginDoc":
        return self


class TestSSOEnsure(unittest.TestCase):
    def setUp(self):
        self.db_store: dict[str, FakeSocialLoginDoc] = {}

        def mock_exists(doctype, name_or_filters):
            if doctype != "Social Login Key":
                return False
            if isinstance(name_or_filters, str):
                return name_or_filters in self.db_store
            if isinstance(name_or_filters, dict):
                provider = name_or_filters.get("provider_name")
                for doc in self.db_store.values():
                    if doc.provider_name == provider:
                        return True
            return False

        def mock_get_doc(doctype, name_or_filters):
            if doctype != "Social Login Key":
                raise ValueError(f"Unknown doctype {doctype}")
            if isinstance(name_or_filters, str):
                if name_or_filters in self.db_store:
                    return self.db_store[name_or_filters]
                doc = FakeSocialLoginDoc(name_or_filters, is_new=False)
                self.db_store[name_or_filters] = doc
                return doc
            if isinstance(name_or_filters, dict):
                provider = name_or_filters.get("provider_name")
                for doc in self.db_store.values():
                    if doc.provider_name == provider:
                        return doc
            raise ValueError(f"Social Login Key not found: {name_or_filters}")

        def mock_new_doc(doctype):
            if doctype != "Social Login Key":
                raise ValueError(f"Unknown doctype {doctype}")
            doc = FakeSocialLoginDoc(frappe.scrub(KEYCLOAK_PROVIDER_NAME), is_new=True)
            self.db_store[doc.name] = doc
            return doc

        def mock_delete_doc(doctype, name, *args, **kwargs):
            if doctype == "Social Login Key":
                self.db_store.pop(name, None)

        def mock_get_all(doctype, filters=None, pluck=None, **kwargs):
            if doctype != "Social Login Key":
                return []
            results = []
            for doc in self.db_store.values():
                if filters and "provider_name" in filters:
                    filter_val = filters["provider_name"]
                    if isinstance(filter_val, list) and filter_val[0] == "in":
                        if doc.provider_name in filter_val[1]:
                            results.append(doc.name if pluck == "name" else doc)
                    elif doc.provider_name == filter_val:
                        results.append(doc.name if pluck == "name" else doc)
                else:
                    results.append(doc.name if pluck == "name" else doc)
            return results

        frappe.db = MagicMock()
        frappe.db.exists = MagicMock(side_effect=mock_exists)
        frappe.db.get_doc = MagicMock(side_effect=mock_get_doc)
        frappe.get_doc = MagicMock(side_effect=mock_get_doc)
        frappe.new_doc = MagicMock(side_effect=mock_new_doc)
        frappe.delete_doc = MagicMock(side_effect=mock_delete_doc)
        frappe.get_all = MagicMock(side_effect=mock_get_all)

        # Clear conf
        if hasattr(frappe, "conf"):
            frappe.conf.clear()

    def test_ensure_social_login_keys_creates_keycloak_only(self):
        """Test creating Keycloak Social Login Key with conf credentials."""
        from elms.sso.ensure import ensure_social_login_keys

        frappe.conf[KEYCLOAK_LOGIN_CONF_KEY] = {
            "client_id": "test-keycloak-client",
            "client_secret": "test-secret",
        }

        doc_name = ensure_social_login_keys()
        self.assertEqual(doc_name, "keycloak")
        self.assertIn("keycloak", self.db_store)

        doc = self.db_store["keycloak"]
        self.assertEqual(doc.provider_name, KEYCLOAK_PROVIDER_NAME)
        self.assertEqual(doc.social_login_provider, KEYCLOAK_PROVIDER_NAME)
        self.assertEqual(doc.custom_base_url, 1)
        self.assertTrue(doc.base_url.endswith(f"/realms/{DEFAULT_KEYCLOAK_REALM}"))
        self.assertNotIn("http://keycloak:8080", doc.base_url)
        self.assertEqual(doc.user_id_property, "sub")
        self.assertEqual(doc.enable_social_login, 1)
        self.assertEqual(doc.client_id, "test-keycloak-client")
        self.assertEqual(doc.client_secret, "test-secret")
        self.assertEqual(doc.redirect_url, KEYCLOAK_DEFAULT_REDIRECT_URL)
        self.assertEqual(doc.sign_ups, "Allow")

        auth_data = json.loads(doc.auth_url_data)
        self.assertEqual(auth_data.get("response_type"), "code")
        self.assertIn("openid", auth_data.get("scope", ""))
        self.assertIn("email", auth_data.get("scope", ""))
        self.assertIn("profile", auth_data.get("scope", ""))

    def test_ensure_social_login_keys_idempotent(self):
        """Test that calling ensure_social_login_keys repeatedly does not duplicate rows."""
        from elms.sso.ensure import ensure_social_login_keys

        frappe.conf[KEYCLOAK_LOGIN_CONF_KEY] = {
            "client_id": "test-client-id",
            "client_secret": "test-client-secret",
        }

        name1 = ensure_social_login_keys()
        name2 = ensure_social_login_keys()
        self.assertEqual(name1, name2)
        self.assertEqual(len(self.db_store), 1)

    def test_ensure_social_login_keys_disabled_without_conf(self):
        """Test that missing conf credentials sets enable_social_login to 0 (BN-001 / TM-001)."""
        from elms.sso.ensure import ensure_social_login_keys

        # Ensure no conf credentials
        frappe.conf.clear()

        doc_name = ensure_social_login_keys()
        self.assertEqual(doc_name, "keycloak")
        doc = self.db_store["keycloak"]
        self.assertEqual(doc.enable_social_login, 0)

    def test_ensure_social_login_keys_uses_keycloak_redirect_only(self):
        """Test that redirect_url is strictly login_via_keycloak and no custom callback is set."""
        from elms.sso.ensure import ensure_social_login_keys

        ensure_social_login_keys()
        doc = self.db_store["keycloak"]
        self.assertEqual(
            doc.redirect_url,
            "/api/method/frappe.integrations.oauth2_logins.login_via_keycloak",
        )
        self.assertNotIn("custom", doc.redirect_url)

    def test_no_direct_yandex_social_login_key(self):
        """Test that preexisting direct Yandex Social Login Key is deleted and only Keycloak exists."""
        from elms.sso.ensure import ensure_social_login_keys

        # Prepopulate direct Yandex key in mock DB
        yandex_key = FakeSocialLoginDoc("yandex", is_new=False)
        yandex_key.provider_name = "Yandex"
        self.db_store["yandex"] = yandex_key

        ensure_social_login_keys()

        # Direct yandex row must be purged
        self.assertNotIn("yandex", self.db_store)
        self.assertEqual(list(self.db_store.keys()), ["keycloak"])

    def test_signups_deny_mode_configured(self):
        """Test that sign_ups can be set to Deny when requested (BN-003 / TM-003)."""
        from elms.sso.ensure import ensure_social_login_keys

        frappe.conf[KEYCLOAK_LOGIN_CONF_KEY] = {
            "client_id": "test-client",
            "client_secret": "test-secret",
        }

        # Case A: Explicit parameter
        ensure_social_login_keys(sign_ups="Deny")
        doc = self.db_store["keycloak"]
        self.assertEqual(doc.sign_ups, "Deny")

        # Case B: Conf setting
        frappe.conf[KEYCLOAK_LOGIN_CONF_KEY]["sign_ups"] = "Deny"
        ensure_social_login_keys()
        doc = self.db_store["keycloak"]
        self.assertEqual(doc.sign_ups, "Deny")


if __name__ == "__main__":
    unittest.main()
