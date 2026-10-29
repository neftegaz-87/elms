import json
import os
from typing import Any

import frappe

ELMS_ADMIN_ROLE: str = "ELMS Admin"
ELMS_OPERATIONS_USER_ROLE: str = "ELMS Operations User"
ELMS_LMS_USER_ROLE: str = "ELMS LMS User"

ELMS_ROLES: tuple[str, ...] = (
    ELMS_ADMIN_ROLE,
    ELMS_OPERATIONS_USER_ROLE,
    ELMS_LMS_USER_ROLE,
)

ELMS_OPERATIONS_SECTION_DOCTYPE: str = "ELMS Operations Section"
ELMS_LMS_SECTION_DOCTYPE: str = "ELMS LMS Section"
ELMS_SETTINGS_SECTION_DOCTYPE: str = "ELMS Settings Section"

SECTION_DOCTYPES: tuple[str, ...] = (
    ELMS_OPERATIONS_SECTION_DOCTYPE,
    ELMS_LMS_SECTION_DOCTYPE,
    ELMS_SETTINGS_SECTION_DOCTYPE,
)

SECTION_DOCPERM_MATRIX: dict[str, list[dict[str, Any]]] = {
    ELMS_OPERATIONS_SECTION_DOCTYPE: [
        {"role": ELMS_ADMIN_ROLE, "read": 1, "write": 1, "create": 1, "delete": 1},
        {"role": ELMS_OPERATIONS_USER_ROLE, "read": 1, "write": 1, "create": 0, "delete": 0},
    ],
    ELMS_LMS_SECTION_DOCTYPE: [
        {"role": ELMS_ADMIN_ROLE, "read": 1, "write": 1, "create": 1, "delete": 1},
        {"role": ELMS_LMS_USER_ROLE, "read": 1, "write": 1, "create": 0, "delete": 0},
    ],
    ELMS_SETTINGS_SECTION_DOCTYPE: [
        {"role": ELMS_ADMIN_ROLE, "read": 1, "write": 1, "create": 1, "delete": 1},
    ],
}

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

if not hasattr(frappe, "ValidationError"):
    class ValidationError(Exception):
        pass
    frappe.ValidationError = ValidationError


class YandexSMTPDeliveryError(frappe.ValidationError):
    """Raised when Yandex SMTP delivery fails; masking delivery failure is forbidden (FR-016)."""

    pass


def ensure_roles() -> None:
    """Idempotently ensure required ELMS roles exist in Frappe.

    Fail-closed: if any role fails to create or is missing after creation,
    raises frappe.throw. Swallowing exceptions with try/except pass is strictly forbidden (AC--1).
    """
    for role_name in ELMS_ROLES:
        if not frappe.db.exists("Role", role_name):
            doc = frappe.new_doc("Role")
            doc.role_name = role_name
            doc.flags.ignore_permissions = True
            doc.insert()

    # Fail-closed verification
    for role_name in ELMS_ROLES:
        if not frappe.db.exists("Role", role_name):
            frappe.throw(f"ELMS role '{role_name}' could not be created or found after ensure_roles.")


def ensure_section_perms() -> None:
    """Idempotently ensure required DocPerm entries for ELMS section DocTypes (FR-004, FR-005).

    Synchronizes permissions across ELMS section DocTypes:
    - ELMS Admin: full RWCD on Operations, LMS, Settings sections.
    - ELMS Operations User: RW on Operations section only.
    - ELMS LMS User: RW on LMS section only.
    - Guest / Other roles: strictly denied access.
    """
    if not hasattr(frappe, "db") or frappe.db is None:
        frappe.throw("Database connection is not available for ensure_section_perms.")

    if not frappe.db.exists("DocType", "Custom DocPerm"):
        frappe.throw("Required DocType 'Custom DocPerm' not found for ensure_section_perms.")

    for doctype_name, perms in SECTION_DOCPERM_MATRIX.items():
        if not frappe.db.exists("DocType", doctype_name):
            frappe.throw(f"Required DocType '{doctype_name}' not found for ensure_section_perms.")

        for perm in perms:
            role = perm["role"]
            custom_perm_name = frappe.db.get_value(
                "Custom DocPerm",
                {"parent": doctype_name, "role": role, "permlevel": 0},
                "name",
            )
            if custom_perm_name:
                doc = frappe.get_doc("Custom DocPerm", custom_perm_name)
                doc.update(perm)
                doc.flags.ignore_permissions = True
                doc.save()
            else:
                doc = frappe.new_doc("Custom DocPerm")
                doc.parent = doctype_name
                doc.parenttype = "DocType"
                doc.parentfield = "permissions"
                doc.permlevel = 0
                doc.update(perm)
                doc.flags.ignore_permissions = True
                doc.insert()


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
            "auth_method": "Basic",
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


def after_migrate() -> None:
    """Post-migration hook for ELMS app.

    Idempotently ensures required ELMS roles, section permissions, and Social Login Key exist.
    """
    ensure_roles()
    ensure_section_perms()
    from elms.sso.ensure import ensure_social_login_keys
    ensure_social_login_keys()


def after_install() -> None:
    """Post-installation hook for ELMS app.

    Sets up Keycloak Social Login Key, Yandex SMTP configuration,
    and ensures required ELMS roles and section permissions exist.
    """
    ensure_roles()
    ensure_section_perms()

    try:
        from elms.sso.ensure import ensure_social_login_keys
        ensure_social_login_keys()
    except Exception as e:
        frappe.log_error(title="ELMS ensure_social_login_keys error", message=str(e))
        raise

    try:
        setup_yandex_smtp()
    except Exception as e:
        frappe.log_error(title="ELMS setup_yandex_smtp error", message=str(e))
        raise
