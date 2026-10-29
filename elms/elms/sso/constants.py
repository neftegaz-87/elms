"""Canonical SSO constants for ELMS Keycloak and Yandex authentication."""

KEYCLOAK_PROVIDER_NAME: str = "Keycloak"
YANDEX_IDP_ALIAS: str = "yandex"

KEYCLOAK_LOGIN_CONF_KEY: str = "keycloak_login"

DEFAULT_SSO_ROLES: tuple[str, ...] = ("Desk User", "ELMS LMS User")
DEFAULT_SSO_ROLES_CONF_KEY: str = "elms_sso_default_roles"

KEYCLOAK_DEFAULT_REDIRECT_URL: str = (
    "/api/method/frappe.integrations.oauth2_logins.login_via_keycloak"
)

YANDEX_AUTH_URL: str = "https://oauth.yandex.ru/authorize"
YANDEX_TOKEN_URL: str = "https://oauth.yandex.ru/token"
YANDEX_USERINFO_URL: str = "https://login.yandex.ru/info"

DEFAULT_KEYCLOAK_REALM: str = "elms"
DEFAULT_KEYCLOAK_CLIENT_ID: str = "elms-frappe"

ENV_KEYCLOAK_CLIENT_ID: str = "KEYCLOAK_CLIENT_ID"
ENV_KEYCLOAK_CLIENT_SECRET: str = "KEYCLOAK_CLIENT_SECRET"
ENV_KEYCLOAK_PUBLIC_URL: str = "KEYCLOAK_PUBLIC_URL"
ENV_YANDEX_CLIENT_ID: str = "YANDEX_CLIENT_ID"
ENV_YANDEX_CLIENT_SECRET: str = "YANDEX_CLIENT_SECRET"
ENV_ELMS_SSO_DEFAULT_ROLES: str = "ELMS_SSO_DEFAULT_ROLES"
ENV_ELMS_SSO_REQUIRE: str = "ELMS_SSO_REQUIRE"
