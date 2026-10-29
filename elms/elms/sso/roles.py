"""SSO role assignment hook for just-in-time provisioned Keycloak users."""

from __future__ import annotations

import frappe
from elms.sso.constants import (
    DEFAULT_SSO_ROLES,
    DEFAULT_SSO_ROLES_CONF_KEY,
    KEYCLOAK_PROVIDER_NAME,
)


def _(text: str) -> str:
    """Safe translation wrapper compatible with pure-Python test environments."""
    if hasattr(frappe, "_") and callable(frappe._):
        return frappe._(text)
    return text


def get_default_sso_roles() -> list[str]:
    """Retrieve default SSO roles from site configuration or fallback to canonical constants."""
    conf_roles = None
    if hasattr(frappe, "conf") and frappe.conf:
        conf_roles = frappe.conf.get(DEFAULT_SSO_ROLES_CONF_KEY)

    if conf_roles:
        if isinstance(conf_roles, str):
            return [r.strip() for r in conf_roles.split(",") if r.strip()]
        if isinstance(conf_roles, (list, tuple)):
            return [str(r).strip() for r in conf_roles if str(r).strip()]

    return list(DEFAULT_SSO_ROLES)


def is_keycloak_social_user(doc) -> bool:
    """Determine whether a Frappe User document was created via Keycloak social login."""
    flags = getattr(doc, "flags", None)
    if flags:
        provider_flag = getattr(flags, "social_login_provider", None)
        if provider_flag and str(provider_flag).lower() == "keycloak":
            return True

    social_logins = getattr(doc, "social_logins", None)
    if social_logins:
        for entry in social_logins:
            provider = entry.get("provider") if isinstance(entry, dict) else getattr(entry, "provider", None)
            if provider and str(provider).lower() == "keycloak":
                return True

    if hasattr(doc, "get_social_login_userid"):
        if doc.get_social_login_userid("keycloak") or doc.get_social_login_userid(KEYCLOAK_PROVIDER_NAME):
            return True

    return False


def maybe_assign_sso_roles(doc, method: str | None = None) -> None:
    """Assign default SSO roles to newly created Frappe User on Keycloak social signup.

    Hooked into Frappe doc_events User after_insert.
    Fails closed if verified email is missing or if any configured default role is missing from DB.
    Ignores non-social users or users created via other providers.
    """
    flags = getattr(doc, "flags", None)
    if flags and getattr(flags, "in_sso_role_assignment", False):
        return

    if not is_keycloak_social_user(doc):
        return

    # BN-004 / TM-004: Validate Keycloak-derived verified email fail-closed
    email = getattr(doc, "email", None)
    if not email or not str(email).strip():
        frappe.throw(
            _("SSO user creation requires a valid verified email address fail-closed."),
            exc=getattr(frappe, "ValidationError", Exception),
        )

    # BN-005 / TM-005: Validate that all default roles exist in the database fail-closed
    default_roles = get_default_sso_roles()
    if hasattr(frappe, "db") and hasattr(frappe.db, "exists"):
        for role in default_roles:
            if not frappe.db.exists("Role", role):
                frappe.throw(
                    _("Default SSO role '{0}' does not exist. Fail-closed signup aborted.").format(role),
                    exc=getattr(frappe, "ValidationError", Exception),
                )

    existing_roles = set()
    if hasattr(doc, "get_roles"):
        try:
            existing_roles = set(doc.get_roles() or [])
        except Exception:
            pass

    if not existing_roles and getattr(doc, "roles", None):
        for r in doc.roles:
            role_name = r.get("role") if isinstance(r, dict) else getattr(r, "role", None)
            if role_name:
                existing_roles.add(role_name)

    roles_to_add = [r for r in default_roles if r not in existing_roles]
    if not roles_to_add:
        return

    if flags:
        flags.in_sso_role_assignment = True

    try:
        if hasattr(doc, "add_roles"):
            doc.add_roles(*roles_to_add)
        else:
            for r in roles_to_add:
                doc.append("roles", {"role": r})
    finally:
        if flags:
            flags.in_sso_role_assignment = False
