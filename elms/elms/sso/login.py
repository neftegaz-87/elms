"""Keycloak broker authorization for the standard ELMS login form."""

from __future__ import annotations

import os
from urllib.parse import urlencode, urlparse

import frappe
if not hasattr(frappe, "whitelist"):
    def _whitelist(*args, **kwargs):
        def decorator(f):
            return f
        if args and callable(args[0]):
            return args[0]
        return decorator
    frappe.whitelist = _whitelist
if not hasattr(frappe, "throw"):
    def _throw(message, exc=Exception, *args, **kwargs):
        raise exc(message)
    frappe.throw = _throw
try:
    from frappe import _
except (ImportError, AttributeError):
    def _(msg: str, *args, **kwargs) -> str:
        return msg

try:
    from frappe.utils.oauth import create_oauth_state
except (ImportError, ModuleNotFoundError):
    create_oauth_state = None

from elms.sso.constants import (
    DEFAULT_KEYCLOAK_CLIENT_ID,
    KEYCLOAK_DEFAULT_REDIRECT_URL,
    KEYCLOAK_LOGIN_CONF_KEY,
    YANDEX_IDP_ALIAS,
)
from elms.sso.ensure import get_keycloak_public_realm_url
from elms.sso.mapping import get_mapping_registry


class KeycloakLoginError(Exception):
    """Raised when Keycloak cannot authenticate the submitted credentials."""


def _get_keycloak_credentials() -> tuple[str, str]:
    config = getattr(frappe, "conf", None)
    credentials = config.get(KEYCLOAK_LOGIN_CONF_KEY) if config and hasattr(config, "get") else None
    if not isinstance(credentials, dict):
        raise KeycloakLoginError("Keycloak client credentials are not configured")

    client_id = str(credentials.get("client_id") or "").strip()
    client_secret = str(credentials.get("client_secret") or "").strip()
    if not client_id or not client_secret:
        raise KeycloakLoginError("Keycloak client credentials are not configured")
    return client_id, client_secret


def _local_keycloak_login_enabled() -> bool:
    """Allow local Keycloak credentials only in an explicitly enabled dev stack."""
    raw = os.getenv("ELMS_ALLOW_LOCAL_KEYCLOAK_LOGIN", "")
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _get_absolute_frappe_callback() -> str:
    """Build the browser-facing OAuth callback accepted by Keycloak.

    Frappe's OAuth endpoint is stored as a relative path in the realm manifest,
    but the authorization request itself must contain an absolute URI.  Use
    Frappe's canonical URL resolver first and keep an environment fallback for
    workers where request/site context is not initialized yet.
    """
    public_url = ""
    try:
        from frappe.utils import get_url

        public_url = str(get_url() or "").strip()
    except Exception:
        # During boot and isolated unit tests Frappe may not have local/site
        # context.  FRAPPE_PUBLIC_URL is the explicit deployment contract.
        public_url = ""

    parsed_url = urlparse(public_url)
    if not (parsed_url.scheme in {"http", "https"} and parsed_url.netloc):
        public_url = (os.getenv("FRAPPE_PUBLIC_URL") or "").strip()

    parsed_url = urlparse(public_url)
    if not (parsed_url.scheme in {"http", "https"} and parsed_url.netloc):
        # Keep the returned URI valid even for a context-less dev invocation.
        # Real containers provide FRAPPE_PUBLIC_URL and never use this value.
        public_url = "http://elms.localhost:8082"

    return f"{public_url.rstrip('/')}/{KEYCLOAK_DEFAULT_REDIRECT_URL.lstrip('/')}"


@frappe.whitelist(allow_guest=True, methods=["GET", "POST"])
def get_sso_authorization_url(
    user_input: str | None = None,
    redirect_to: str | None = "/app",
    mode: str | None = "yandex",
) -> dict[str, str]:
    """Return a Keycloak authorization URL for brokered or local dev login.

    The normal mode always adds ``kc_idp_hint=yandex``. Frappe never receives
    or forwards a password. Local Keycloak login is an explicit dev-only mode
    for seeded test accounts and is rejected unless the dev flag is enabled.
    """
    resolved_mode = str(mode or "yandex").strip().lower()
    if resolved_mode not in {"yandex", "local"}:
        frappe.throw(_("Unsupported SSO login mode."))
    if resolved_mode == "local" and not _local_keycloak_login_enabled():
        frappe.throw(_("Local Keycloak login is disabled."))

    try:
        client_id, _ = _get_keycloak_credentials()
    except Exception:
        client_id = DEFAULT_KEYCLOAK_CLIENT_ID

    realm_url = get_keycloak_public_realm_url()
    target_identity = get_mapping_registry().resolve_target_identity(user_input or "") if user_input else ""

    params = {
        "client_id": client_id,
        "response_type": "code",
        "scope": "openid profile email",
        "redirect_uri": _get_absolute_frappe_callback(),
    }
    if resolved_mode == "yandex":
        params["kc_idp_hint"] = YANDEX_IDP_ALIAS
    if target_identity and "@" in target_identity:
        params["login_hint"] = target_identity
    if create_oauth_state:
        params["state"] = create_oauth_state(redirect_to or "/app")

    auth_url = f"{realm_url.rstrip('/')}/protocol/openid-connect/auth?{urlencode(params)}"
    return {
        "auth_url": auth_url,
        "target_identity": target_identity,
        "mapped": bool(target_identity and target_identity != user_input),
    }
