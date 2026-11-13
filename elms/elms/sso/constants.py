"""Canonical SSO constants for ELMS Keycloak-only authentication."""

KEYCLOAK_PROVIDER_NAME: str = "Keycloak"

KEYCLOAK_LOGIN_CONF_KEY: str = "keycloak_login"

DEFAULT_SSO_ROLES: tuple[str, ...] = ("Desk User", "ELMS Learner")
DEFAULT_SSO_ROLES_CONF_KEY: str = "elms_sso_default_roles"

KEYCLOAK_DEFAULT_REDIRECT_URL: str = (
    "/api/method/frappe.integrations.oauth2_logins.login_via_keycloak"
)

DEFAULT_KEYCLOAK_REALM: str = "elms"
DEFAULT_KEYCLOAK_CLIENT_ID: str = "elms-frappe"

ENV_KEYCLOAK_CLIENT_ID: str = "KEYCLOAK_CLIENT_ID"
ENV_KEYCLOAK_CLIENT_SECRET: str = "KEYCLOAK_CLIENT_SECRET"
ENV_KEYCLOAK_INTERNAL_URL: str = "KEYCLOAK_INTERNAL_URL"
ENV_KEYCLOAK_PUBLIC_URL: str = "KEYCLOAK_PUBLIC_URL"
ENV_ELMS_SSO_DEFAULT_ROLES: str = "ELMS_SSO_DEFAULT_ROLES"
ENV_ELMS_SSO_REQUIRE: str = "ELMS_SSO_REQUIRE"
