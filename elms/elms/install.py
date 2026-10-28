import json
import os
from typing import Any

import frappe

APPROVED_ROLE_MAPPINGS: dict[str, list[str]] = {
    "Administrators": ["System Manager"],
    "/Administrators": ["System Manager"],
    "Employees": ["Employee"],
    "/Employees": ["Employee"],
    "Instructors": ["Instructor"],
    "/Instructors": ["Instructor"],
    "Students": ["Student"],
    "/Students": ["Student"],
}


class YandexSMTPDeliveryError(frappe.ValidationError):
    """Raised when Yandex SMTP delivery fails; masking delivery failure is forbidden (FR-016)."""

    pass


def setup_keycloak_social_login() -> str:
    """Create or update Keycloak Social Login Key template idempotently."""
    provider_name = "Keycloak"
    key_name = frappe.scrub(provider_name)
    base_url = os.getenv("KEYCLOAK_BASE_URL", "http://keycloak:8080/realms/elms")
    client_id = os.getenv("KEYCLOAK_CLIENT_ID", "elms-frappe")
    client_secret = os.getenv("KEYCLOAK_CLIENT_SECRET", "")

    doc = None
    if frappe.db.exists("Social Login Key", key_name):
        doc = frappe.get_doc("Social Login Key", key_name)
    elif frappe.db.exists("Social Login Key", {"provider_name": provider_name}):
        doc = frappe.get_doc("Social Login Key", {"provider_name": provider_name})
    else:
        doc = frappe.new_doc("Social Login Key")
        doc.provider_name = provider_name

    doc.update(
        {
            "enable_social_login": 1,
            "custom_base_url": 1,
            "base_url": base_url,
            "authorize_url": "/protocol/openid-connect/auth",
            "access_token_url": "/protocol/openid-connect/token",
            "redirect_url": "/api/method/frappe.integrations.oauth2_logins.login_via_keycloak",
            "api_endpoint": "/protocol/openid-connect/userinfo",
            "client_id": client_id,
            "client_secret": client_secret or None,
            "user_id_property": "preferred_username",
            "auth_url_data": json.dumps({"response_type": "code", "scope": "openid email profile"}),
            "sign_ups": "Allow",
        }
    )

    doc.flags.ignore_permissions = True
    if doc.is_new():
        doc.insert()
    else:
        doc.save()

    return doc.name


def reconcile_keycloak_user(user_doc, keycloak_data: dict[str, Any]) -> None:
    """Idempotent one-way identity lifecycle and role reconciliation: Keycloak -> Frappe.

    Reconciles active status, core profile attributes, and approved group-to-role mappings.
    Does not replace or overwrite existing Frappe DocType permissions.
    Bidirectional role synchronization back to Keycloak is strictly prohibited.
    """
    if not user_doc or not keycloak_data:
        return

    # 1. Lifecycle status sync
    if "enabled" in keycloak_data:
        user_doc.enabled = 1 if keycloak_data["enabled"] else 0

    # 2. Profile attributes update
    if first_name := keycloak_data.get("firstName") or keycloak_data.get("first_name"):
        user_doc.first_name = first_name
    if last_name := keycloak_data.get("lastName") or keycloak_data.get("last_name"):
        user_doc.last_name = last_name

    # 3. Approved group-to-role mapping
    groups = keycloak_data.get("groups") or []
    if isinstance(groups, str):
        groups = [groups]

    roles_to_add: set[str] = set()
    for group in groups:
        if group in APPROVED_ROLE_MAPPINGS:
            for role_name in APPROVED_ROLE_MAPPINGS[group]:
                if frappe.db.exists("Role", role_name):
                    roles_to_add.add(role_name)

    existing_roles = {r.role for r in getattr(user_doc, "roles", [])}
    for role in roles_to_add:
        if role not in existing_roles:
            user_doc.add_roles(role)

    user_doc.flags.ignore_permissions = True
    user_doc.save()


def on_login_sync_identity(login_manager=None) -> None:
    """Hook called on user login.

    If user logged in via Keycloak SSO, ensure one-way identity reconciliation is executed.
    """
    if not login_manager or not getattr(login_manager, "user", None):
        return

    user_email = login_manager.user
    if user_email in ("Administrator", "Guest"):
        return

    oauth_user_data = getattr(frappe.local, "oauth_user_data", None)
    if oauth_user_data and isinstance(oauth_user_data, dict):
        if frappe.db.exists("User", user_email):
            user_doc = frappe.get_doc("User", user_email)
            reconcile_keycloak_user(user_doc, oauth_user_data)


def setup_yandex_smtp() -> str:
    """Configure template Email Account for Yandex 360 SMTP (FR-016 boundary).

    Outage and delivery failures must fail closed and never be masked as success.
    """
    account_name = "Yandex SMTP"
    smtp_server = os.getenv("YANDEX_SMTP_SERVER", "smtp.yandex.ru")
    smtp_port = int(os.getenv("YANDEX_SMTP_PORT", "465"))
    smtp_user = os.getenv("YANDEX_SMTP_USER", "")
    smtp_password = os.getenv("YANDEX_SMTP_PASSWORD", "")

    doc = None
    if frappe.db.exists("Email Account", account_name):
        doc = frappe.get_doc("Email Account", account_name)
    else:
        doc = frappe.new_doc("Email Account")
        doc.email_account_name = account_name

    doc.update(
        {
            "email_id": smtp_user or "noreply@elms.local",
            "smtp_server": smtp_server,
            "smtp_port": smtp_port,
            "use_ssl": 1,
            "enable_outgoing": 1,
            "default_outgoing": 1,
            "auth_method": "LOGIN",
            "password": smtp_password or None,
        }
    )

    doc.flags.ignore_permissions = True
    if doc.is_new():
        doc.insert()
    else:
        doc.save()

    return doc.name


def handle_yandex_smtp_outage(error: Exception) -> None:
    """Explicit failure handling for unavailable Yandex SMTP delivery (FR-016).

    Forbidden to mask or catch-and-suppress SMTP transmission errors.
    """
    error_msg = f"Yandex SMTP service unavailable or delivery failed: {error}"
    frappe.log_error(title="Yandex SMTP Delivery Failure", message=error_msg)
    raise YandexSMTPDeliveryError(error_msg) from error


def after_install() -> None:
    """Post-installation hook for ELMS app.

    Sets up Keycloak Social Login Key template and Yandex SMTP configuration.
    """
    try:
        setup_keycloak_social_login()
    except Exception as e:
        frappe.log_error(title="ELMS setup_keycloak_social_login error", message=str(e))
        raise

    try:
        setup_yandex_smtp()
    except Exception as e:
        frappe.log_error(title="ELMS setup_yandex_smtp error", message=str(e))
        raise
