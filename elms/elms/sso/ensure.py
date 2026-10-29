"""Idempotent Keycloak-only Social Login Key configuration for ELMS."""

from __future__ import annotations

import json
import os
from typing import Any

import frappe
from elms.sso.constants import (
    DEFAULT_KEYCLOAK_REALM,
    ENV_KEYCLOAK_PUBLIC_URL,
    KEYCLOAK_DEFAULT_REDIRECT_URL,
    KEYCLOAK_LOGIN_CONF_KEY,
    KEYCLOAK_PROVIDER_NAME,
    YANDEX_IDP_ALIAS,
)


def _scrub(text: str) -> str:
    """Scrub provider name to slug format matching Frappe conventions."""
    if hasattr(frappe, "scrub") and callable(frappe.scrub):
        return frappe.scrub(text)
    return text.replace(" ", "_").replace("-", "_").lower()


def get_keycloak_public_realm_url(custom_base_url: str | None = None) -> str:
    """Resolve the public browser-facing Keycloak realm URL.

    The browser must never receive the container-only internal address (FR-003).
    """
    if custom_base_url:
        url = custom_base_url.strip().rstrip("/")
        if not url.endswith(f"/realms/{DEFAULT_KEYCLOAK_REALM}"):
            url = f"{url}/realms/{DEFAULT_KEYCLOAK_REALM}"
        return url

    # 1. Check frappe.conf
    if hasattr(frappe, "conf") and frappe.conf:
        if hasattr(frappe.conf, "get"):
            conf_url = frappe.conf.get("keycloak_base_url") or frappe.conf.get("keycloak_public_url")
        else:
            conf_url = getattr(frappe.conf, "keycloak_base_url", None) or getattr(frappe.conf, "keycloak_public_url", None)
        if conf_url:
            url = str(conf_url).strip().rstrip("/")
            if not url.endswith(f"/realms/{DEFAULT_KEYCLOAK_REALM}"):
                url = f"{url}/realms/{DEFAULT_KEYCLOAK_REALM}"
            return url

    # 2. Check environment variables
    env_public = (os.getenv(ENV_KEYCLOAK_PUBLIC_URL) or os.getenv("KEYCLOAK_BASE_URL") or "").strip()
    if env_public:
        url = env_public.rstrip("/")
        if not url.endswith(f"/realms/{DEFAULT_KEYCLOAK_REALM}"):
            url = f"{url}/realms/{DEFAULT_KEYCLOAK_REALM}"
        return url

    # 3. Default dev URL
    return f"http://127.0.0.1:8480/realms/{DEFAULT_KEYCLOAK_REALM}"


def _get_conf_keycloak_credentials() -> dict[str, Any] | None:
    """Retrieve keycloak credentials strictly from frappe.conf."""
    if not hasattr(frappe, "conf") or frappe.conf is None:
        return None
    if hasattr(frappe.conf, "get"):
        return frappe.conf.get(KEYCLOAK_LOGIN_CONF_KEY)
    return getattr(frappe.conf, KEYCLOAK_LOGIN_CONF_KEY, None)


def _purge_forbidden_direct_idp_providers() -> None:
    """Ensure no direct external IdP (such as Yandex) Social Login Key exists.

    Yandex belongs strictly inside Keycloak as an OIDC broker (FR-004, SC-001).
    """
    forbidden_aliases = [YANDEX_IDP_ALIAS, YANDEX_IDP_ALIAS.capitalize()]
    for alias in forbidden_aliases:
        if hasattr(frappe, "db") and frappe.db and hasattr(frappe.db, "exists"):
            if frappe.db.exists("Social Login Key", alias):
                frappe.delete_doc("Social Login Key", alias, force=True, ignore_permissions=True)

    if hasattr(frappe, "get_all") and callable(frappe.get_all):
        try:
            records = frappe.get_all(
                "Social Login Key",
                filters={"provider_name": ["in", forbidden_aliases]},
                pluck="name",
            )
            for record_name in records:
                frappe.delete_doc("Social Login Key", record_name, force=True, ignore_permissions=True)
        except Exception:
            pass


def ensure_social_login_keys(
    sign_ups: str | None = None,
    base_url: str | None = None,
) -> str:
    """Idempotently configure exactly one Social Login Key for Keycloak.

    - Exposes only Keycloak to Frappe login (FR-003, FR-010, US-001).
    - Removes any direct Yandex Social Login Key if present (SC-001).
    - Uses exact canonical Frappe redirect URL: login_via_keycloak (AC-2).
    - Gates enable_social_login strictly on credentials presence in frappe.conf (SC-002, BN-001).
    - Sets user_id_property to 'sub' for immutable subject identity.
    - Supports sign_ups configuration (Allow/Deny) (US-006, BN-003).
    """
    _purge_forbidden_direct_idp_providers()

    key_name = _scrub(KEYCLOAK_PROVIDER_NAME)
    realm_url = get_keycloak_public_realm_url(custom_base_url=base_url)

    # Resolve credentials from frappe.conf
    conf_creds = _get_conf_keycloak_credentials()
    client_id: str | None = None
    client_secret: str | None = None
    enable_social_login: int = 0

    if isinstance(conf_creds, dict):
        raw_id = conf_creds.get("client_id")
        raw_secret = conf_creds.get("client_secret")
        clean_id = str(raw_id).strip() if raw_id is not None else ""
        clean_secret = str(raw_secret).strip() if raw_secret is not None else ""
        if clean_id and clean_secret:
            client_id = clean_id
            client_secret = clean_secret
            enable_social_login = 1
        elif clean_id:
            client_id = clean_id

    # Resolve sign_ups policy
    resolved_sign_ups = "Allow"
    if sign_ups in ("Allow", "Deny"):
        resolved_sign_ups = sign_ups
    elif isinstance(conf_creds, dict) and conf_creds.get("sign_ups") in ("Allow", "Deny"):
        resolved_sign_ups = str(conf_creds["sign_ups"])
    elif hasattr(frappe, "conf") and frappe.conf and hasattr(frappe.conf, "get"):
        conf_sign_ups = frappe.conf.get("keycloak_sign_ups")
        if conf_sign_ups in ("Allow", "Deny"):
            resolved_sign_ups = conf_sign_ups
    elif env_sign_ups := os.getenv("KEYCLOAK_SIGN_UPS"):
        if env_sign_ups in ("Allow", "Deny"):
            resolved_sign_ups = env_sign_ups

    # Retrieve or create Social Login Key
    doc = None
    if frappe.db.exists("Social Login Key", key_name):
        doc = frappe.get_doc("Social Login Key", key_name)
    elif frappe.db.exists("Social Login Key", {"provider_name": KEYCLOAK_PROVIDER_NAME}):
        doc = frappe.get_doc("Social Login Key", {"provider_name": KEYCLOAK_PROVIDER_NAME})
    else:
        doc = frappe.new_doc("Social Login Key")
        doc.provider_name = KEYCLOAK_PROVIDER_NAME

    doc_data = {
        "provider_name": KEYCLOAK_PROVIDER_NAME,
        "social_login_provider": KEYCLOAK_PROVIDER_NAME,
        "custom_base_url": 1,
        "base_url": realm_url,
        "authorize_url": "/protocol/openid-connect/auth",
        "access_token_url": "/protocol/openid-connect/token",
        "redirect_url": KEYCLOAK_DEFAULT_REDIRECT_URL,
        "api_endpoint": "/protocol/openid-connect/userinfo",
        "auth_url_data": json.dumps({"response_type": "code", "scope": "openid email profile"}),
        "user_id_property": "sub",
        "sign_ups": resolved_sign_ups,
        "enable_social_login": enable_social_login,
        "client_id": client_id,
        "client_secret": client_secret,
    }

    doc.update(doc_data)
    doc.flags.ignore_permissions = True

    if doc.is_new():
        doc.insert()
    else:
        doc.save()

    return doc.name
