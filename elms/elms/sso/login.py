"""Server-side Keycloak password authentication for the standard ELMS login form."""

from __future__ import annotations

import os
from typing import Any
from urllib.parse import urljoin, urlparse

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
    from frappe.rate_limiter import rate_limit
except (ImportError, ModuleNotFoundError):
    def rate_limit(*args, **kwargs):
        def decorator(f):
            return f
        return decorator

try:
    import frappe.utils
except (ImportError, ModuleNotFoundError):
    pass

try:
    from frappe.utils.oauth import create_oauth_state, login_oauth_user
except (ImportError, ModuleNotFoundError):
    create_oauth_state = None
    login_oauth_user = None

from requests.exceptions import RequestException

from elms.sso.constants import (
    DEFAULT_KEYCLOAK_CLIENT_ID,
    DEFAULT_KEYCLOAK_REALM,
    KEYCLOAK_DEFAULT_REDIRECT_URL,
    KEYCLOAK_LOGIN_CONF_KEY,
    YANDEX_IDP_ALIAS,
)
from elms.sso.ensure import get_keycloak_public_realm_url
from elms.sso.mapping import get_mapping_registry
from urllib.parse import urlencode

KEYCLOAK_INTERNAL_URL_ENV = "KEYCLOAK_INTERNAL_URL"
KEYCLOAK_INTERNAL_URL_DEFAULT = "http://keycloak:8080"
REQUEST_TIMEOUT_SECONDS = 10


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


def _get_keycloak_internal_url() -> str:
    base_url = (os.getenv(KEYCLOAK_INTERNAL_URL_ENV) or KEYCLOAK_INTERNAL_URL_DEFAULT).strip().rstrip("/")
    parsed = urlparse(base_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise KeycloakLoginError("Keycloak internal URL is invalid")
    return base_url


def _keycloak_endpoint(base_url: str, path: str) -> str:
    return urljoin(f"{base_url}/", f"realms/{DEFAULT_KEYCLOAK_REALM}/{path.lstrip('/')}")


def _response_json(response: Any) -> dict[str, Any]:
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise KeycloakLoginError("Keycloak returned an invalid response")
    return payload


def _normalise_identity(userinfo: dict[str, Any]) -> dict[str, Any]:
    subject = str(userinfo.get("sub") or "").strip()
    email = str(userinfo.get("email") or "").strip().lower()
    if not subject or not email:
        raise KeycloakLoginError("Keycloak identity has no subject or email")

    username = str(userinfo.get("preferred_username") or email).strip()
    first_name = str(userinfo.get("given_name") or userinfo.get("name") or username).strip()
    last_name = str(userinfo.get("family_name") or "").strip()

    return {
        **userinfo,
        "sub": subject,
        "email": email,
        "login": username,
        "first_name": first_name,
        "last_name": last_name,
    }


def authenticate_keycloak(username: str, password: str) -> dict[str, Any]:
    if not username or not password or len(password) > 512:
        raise KeycloakLoginError("Invalid login credentials")

    # Resolve Bitrix source email / login to canonical Yandex / Keycloak identity
    target_username = get_mapping_registry().resolve_target_identity(username)

    client_id, client_secret = _get_keycloak_credentials()
    base_url = _get_keycloak_internal_url()
    session = frappe.utils.get_request_session()

    try:
        token_response = session.post(
            _keycloak_endpoint(base_url, "protocol/openid-connect/token"),
            data={
                "grant_type": "password",
                "client_id": client_id,
                "client_secret": client_secret,
                "username": target_username,
                "password": password,
                "scope": "openid profile email",
            },
            headers={"Accept": "application/json"},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        token = _response_json(token_response).get("access_token")
        if not token:
            raise KeycloakLoginError("Keycloak did not return an access token")

        userinfo_response = session.get(
            _keycloak_endpoint(base_url, "protocol/openid-connect/userinfo"),
            headers={"Accept": "application/json", "Authorization": f"Bearer {token}"},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        return _normalise_identity(_response_json(userinfo_response))
    except (RequestException, ValueError, TypeError) as error:
        raise KeycloakLoginError("Keycloak authentication failed") from error


def _raise_invalid_login() -> None:
	frappe.throw(_("Invalid Login. Try again."), frappe.ValidationError)


@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(limit=10, seconds=60)
def login_with_keycloak(usr: str | None = None, pwd: str | None = None) -> dict[str, str]:
    username = str(usr or "").strip()
    password = pwd or ""
    if not username or not password:
        _raise_invalid_login()

    try:
        identity = authenticate_keycloak(username, password)
        oauth_state = create_oauth_state("/app")
        frappe.local.oauth_user_data = identity
        permission_flags = getattr(frappe, "flags", None)
        if permission_flags is None:
            permission_flags = getattr(getattr(frappe, "local", None), "flags", None)
        previous_ignore_permissions = (
            getattr(permission_flags, "ignore_permissions", None) if permission_flags is not None else None
        )
        if permission_flags is not None:
            permission_flags.ignore_permissions = True
        try:
            login_oauth_user(
                identity,
                provider="keycloak",
                state=oauth_state,
                generate_login_token=True,
            )
        finally:
            if permission_flags is not None:
                permission_flags.ignore_permissions = previous_ignore_permissions
    except KeycloakLoginError:
        _raise_invalid_login()

    login_token = frappe.response.get("login_token")
    if not login_token:
        _raise_invalid_login()
    return {"login_token": login_token}


@frappe.whitelist(allow_guest=True, methods=["GET", "POST"])
def get_sso_authorization_url(user_input: str | None = None, redirect_to: str | None = "/app") -> dict[str, str]:
    """Return the OIDC broker authorization URL pointing directly to Yandex via Keycloak.

    Resolves Bitrix source email to target Yandex email and attaches kc_idp_hint and login_hint.
    """
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
        "redirect_uri": KEYCLOAK_DEFAULT_REDIRECT_URL,
        "kc_idp_hint": YANDEX_IDP_ALIAS,
    }
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
