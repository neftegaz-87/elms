"""Server-side B2B organization and scope operations."""

from __future__ import annotations

import re
from typing import Any

import frappe
from elms.access.keycloak import (
    KeycloakAdminClient,
    KeycloakAdminSettings,
    KeycloakProvisionError,
)

try:
    from frappe import _
except (ImportError, AttributeError):
    def _(message: str, *args: Any) -> str:
        return message.format(*args) if args else message

if not hasattr(frappe, "whitelist"):
    def _whitelist(*args: Any, **kwargs: Any):
        def decorator(function: Any) -> Any:
            return function
        if args and callable(args[0]):
            return args[0]
        return decorator
    frappe.whitelist = _whitelist

if not hasattr(frappe, "PermissionError"):
    frappe.PermissionError = PermissionError
if not hasattr(frappe, "ValidationError"):
    frappe.ValidationError = ValueError
if not hasattr(frappe, "DoesNotExistError"):
    frappe.DoesNotExistError = LookupError
if not hasattr(frappe, "throw"):
    def _throw_fallback(message: str, exception: type[Exception] = Exception, *args: Any, **kwargs: Any) -> None:
        raise exception(message)
    frappe.throw = _throw_fallback


ELMS_ADMIN_ROLE = "ELMS Admin"
ELMS_COMPANY_ADMIN_ROLE = "ELMS Company Admin"
COMPANY_ADMIN_PROFILE = "ELMS Company Admin Profile"
DEFAULT_INVITE_PROFILE = "ELMS Learner Profile"
ORGANIZATION_DOCTYPE = "ELMS Organization"
MEMBER_DOCTYPE = "ELMS Organization Member"
USER_PERMISSION_DOCTYPE = "User Permission"


def _current_user() -> str:
    return str(getattr(getattr(frappe, "session", None), "user", "Guest") or "Guest")


def _roles(user: str | None = None) -> set[str]:
    current = user or _current_user()
    if current == "Administrator":
        return {"Administrator", "System Manager", ELMS_ADMIN_ROLE}
    get_roles = getattr(frappe, "get_roles", None)
    return set(get_roles(current) or []) if callable(get_roles) else set()


def _is_admin(user: str | None = None) -> bool:
    return bool(_roles(user).intersection({"Administrator", "System Manager", ELMS_ADMIN_ROLE}))


def _throw(message: str, exception: type[Exception] | None = None) -> None:
    error_type = exception or getattr(frappe, "ValidationError", ValueError)
    frappe.throw(_(message), error_type)


def _require_admin() -> None:
    if not _is_admin():
        _throw("Требуется роль ELMS Admin или System Manager", frappe.PermissionError)


def _clean(value: Any, field: str, limit: int = 140) -> str:
    result = str(value or "").strip()
    if not result:
        _throw(f"Поле {field} обязательно", frappe.ValidationError)
    if len(result) > limit:
        _throw(f"Поле {field} слишком длинное", frappe.ValidationError)
    return result


def _db_exists(doctype: str, filters: Any) -> Any:
    db = getattr(frappe, "db", None)
    exists = getattr(db, "exists", None)
    return exists(doctype, filters) if callable(exists) else None


def _new_doc(values: dict[str, Any]) -> Any:
    get_doc = getattr(frappe, "get_doc", None)
    if callable(get_doc):
        return get_doc(values)
    return frappe.new_doc(values["doctype"])


def _insert(doc: Any) -> Any:
    insert = getattr(doc, "insert", None)
    if not callable(insert):
        _throw("Не удалось создать запись ELMS", frappe.ValidationError)
    try:
        return insert(ignore_permissions=True)
    except TypeError:
        return insert()


def _ensure_user_permission(user: str, organization: str) -> str:
    filters = {"user": user, "allow": ORGANIZATION_DOCTYPE, "for_value": organization}
    existing = _db_exists(USER_PERMISSION_DOCTYPE, filters)
    if existing:
        return str(existing)
    permission = _new_doc(
        {
            "doctype": USER_PERMISSION_DOCTYPE,
            "user": user,
            "allow": ORGANIZATION_DOCTYPE,
            "for_value": organization,
            "apply_to_all_doctypes": 1,
        }
    )
    _insert(permission)
    return str(getattr(permission, "name", ""))


def _remove_user_permission(user: str, organization: str) -> None:
    if _db_exists(MEMBER_DOCTYPE, {"user": user, "organization": organization}):
        return
    db = getattr(frappe, "db", None)
    delete = getattr(db, "delete", None)
    if callable(delete):
        delete(
            USER_PERMISSION_DOCTYPE,
            {"user": user, "allow": ORGANIZATION_DOCTYPE, "for_value": organization},
        )


def organization_membership_exists(user: str, organization: str) -> bool:
    """Return whether ``user`` has explicit membership in ``organization``."""
    return bool(_db_exists(MEMBER_DOCTYPE, {"user": user, "organization": organization}))


def require_organization_access(organization: str, user: str | None = None) -> str:
    """Enforce Admin or explicit Company Admin membership for an organization."""
    organization_name = _clean(organization, "organization")
    current = user or _current_user()
    is_company_admin = ELMS_COMPANY_ADMIN_ROLE in _roles(current)
    if _is_admin(current) or (
        is_company_admin and organization_membership_exists(current, organization_name)
    ):
        return organization_name
    _throw("Нет доступа к этой организации", frappe.PermissionError)
    raise AssertionError("frappe.throw must raise")


@frappe.whitelist()
def create_organization(
    name: str,
    inn: str,
    ogrn: str | None = None,
    kpp: str | None = None,
    status: str = "Active",
) -> dict[str, str]:
    """Create an organization boundary; only ELMS admins may create one."""
    _require_admin()
    organization_name = _clean(name, "name")
    inn_value = _clean(inn, "inn", 12)
    status_value = str(status or "Active").strip()
    if status_value not in {"Active", "Inactive"}:
        _throw("Недопустимый статус организации", frappe.ValidationError)
    if _db_exists(ORGANIZATION_DOCTYPE, {"organization_name": organization_name}):
        _throw("Организация с таким названием уже существует", frappe.ValidationError)

    organization = _new_doc(
        {
            "doctype": ORGANIZATION_DOCTYPE,
            "organization_name": organization_name,
            "inn": inn_value,
            "ogrn": str(ogrn or "").strip(),
            "kpp": str(kpp or "").strip(),
            "status": status_value,
        }
    )
    _insert(organization)
    return {"organization": str(getattr(organization, "name", organization_name))}


@frappe.whitelist()
def assign_company_admin(user: str, organization: str) -> dict[str, str]:
    """Assign the Company Admin profile and organization scope to a user."""
    _require_admin()
    user_name = _clean(user, "user", 180)
    organization_name = _clean(organization, "organization")
    if not _db_exists(ORGANIZATION_DOCTYPE, organization_name) and not _db_exists(
        ORGANIZATION_DOCTYPE, {"name": organization_name}
    ):
        _throw("Организация не найдена", frappe.DoesNotExistError)
    if not _db_exists("User", user_name):
        _throw("Пользователь не найден", frappe.DoesNotExistError)

    user_doc = frappe.get_doc("User", user_name)
    user_doc.role_profile_name = COMPANY_ADMIN_PROFILE
    roles = {str(getattr(row, "role", "")) for row in getattr(user_doc, "roles", [])}
    if ELMS_COMPANY_ADMIN_ROLE not in roles:
        append = getattr(user_doc, "append", None)
        if callable(append):
            append("roles", {"role": ELMS_COMPANY_ADMIN_ROLE})
    user_doc.flags.ignore_permissions = True
    save = getattr(user_doc, "save", None)
    if callable(save):
        save()

    if not organization_membership_exists(user_name, organization_name):
        membership = _new_doc(
            {
                "doctype": MEMBER_DOCTYPE,
                "user": user_name,
                "organization": organization_name,
                "role_profile": COMPANY_ADMIN_PROFILE,
                "is_primary": 1,
            }
        )
        _insert(membership)
    _ensure_user_permission(user_name, organization_name)
    return {
        "user": user_name,
        "organization": organization_name,
        "role_profile": COMPANY_ADMIN_PROFILE,
    }


def _get_keycloak_client() -> KeycloakAdminClient:
    return KeycloakAdminClient(KeycloakAdminSettings.from_env())


def _create_or_get_frappe_user(
    email: str,
    first_name: str,
    last_name: str,
    role_profile: str,
) -> tuple[Any, bool]:
    existing = _db_exists("User", email)
    created = not bool(existing)
    if created:
        user_doc = _new_doc(
            {
                "doctype": "User",
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "enabled": 1,
                "send_welcome_email": 0,
                "role_profile_name": role_profile,
            }
        )
    else:
        user_doc = frappe.get_doc("User", email)
        user_doc.first_name = first_name
        user_doc.last_name = last_name
        user_doc.enabled = 1
        user_doc.role_profile_name = role_profile
    roles = {str(getattr(row, "role", "")) for row in getattr(user_doc, "roles", [])}
    for role in ("Desk User", "ELMS Learner"):
        if role not in roles and callable(getattr(user_doc, "append", None)):
            user_doc.append("roles", {"role": role})
    user_doc.flags.ignore_permissions = True
    if created:
        _insert(user_doc)
    elif callable(getattr(user_doc, "save", None)):
        user_doc.save()
    return user_doc, created


def _ensure_membership_and_scope(user: str, organization: str, role_profile: str) -> None:
    if not organization_membership_exists(user, organization):
        membership = _new_doc(
            {
                "doctype": MEMBER_DOCTYPE,
                "user": user,
                "organization": organization,
                "role_profile": role_profile,
                "is_primary": 1,
            }
        )
        _insert(membership)
    _ensure_user_permission(user, organization)


def _record_invite_log(
    email: str,
    organization: str,
    status: str,
    keycloak_user_id: str = "",
    error_message: str = "",
) -> None:
    db = getattr(frappe, "db", None)
    if not db or not callable(getattr(db, "exists", None)):
        return
    if not db.exists("DocType", "ELMS Invite Log"):
        return
    log = _new_doc(
        {
            "doctype": "ELMS Invite Log",
            "email": email,
            "organization": organization,
            "invited_by": _current_user(),
            "keycloak_user_id": keycloak_user_id,
            "status": status,
            "error_message": error_message[:500],
        }
    )
    _insert(log)


def _disable_new_user(user_doc: Any) -> None:
    user_doc.enabled = 0
    flags = getattr(user_doc, "flags", None)
    if flags is not None:
        flags.ignore_permissions = True
    save = getattr(user_doc, "save", None)
    if callable(save):
        save()


@frappe.whitelist()
def invite_org_user(
    email: str,
    first_name: str,
    last_name: str,
    organization: str,
    role_profile: str | None = None,
) -> dict[str, Any]:
    """Provision a user in Frappe and Keycloak for an authorized organization."""
    email_value = _clean(email, "email", 180).casefold()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email_value):
        _throw("Укажите корректный email", frappe.ValidationError)
    first_name_value = _clean(first_name, "first_name", 120)
    last_name_value = _clean(last_name, "last_name", 120)
    organization_value = require_organization_access(organization)
    profile = str(role_profile or DEFAULT_INVITE_PROFILE).strip()
    if profile not in {DEFAULT_INVITE_PROFILE, COMPANY_ADMIN_PROFILE}:
        _throw("Недопустимый профиль приглашения", frappe.ValidationError)

    user_doc, created = _create_or_get_frappe_user(
        email_value, first_name_value, last_name_value, profile
    )
    _ensure_membership_and_scope(str(getattr(user_doc, "name", email_value)), organization_value, profile)
    client = _get_keycloak_client()
    keycloak_user_id = ""
    try:
        keycloak_user_id = client.upsert_user(email_value, first_name_value, last_name_value)
        client.send_password_setup(keycloak_user_id)
    except KeycloakProvisionError as error:
        if created:
            _disable_new_user(user_doc)
        _record_invite_log(email_value, organization_value, "Failed", error_message=str(error))
        raise
    except Exception as error:
        if created:
            _disable_new_user(user_doc)
        typed_error = KeycloakProvisionError("Keycloak invite failed")
        _record_invite_log(email_value, organization_value, "Failed", error_message=str(typed_error))
        raise typed_error from error

    _record_invite_log(email_value, organization_value, "Invited", keycloak_user_id=keycloak_user_id)
    return {
        "user": str(getattr(user_doc, "name", email_value)),
        "organization": organization_value,
        "keycloak_id": keycloak_user_id,
        "invited": True,
        "status": "invited",
    }


def _legacy_social_logins(user_doc: Any) -> list[Any]:
    rows = getattr(user_doc, "social_logins", None) or []
    legacy_rows: list[Any] = []
    for row in rows:
        provider = row.get("provider") if isinstance(row, dict) else getattr(row, "provider", "")
        if str(provider or "").strip().casefold() in {"yandex", "yandex 360"}:
            legacy_rows.append(row)
    return legacy_rows


def _set_social_login_value(row: Any, field: str, value: str) -> None:
    if isinstance(row, dict):
        row[field] = value
    else:
        setattr(row, field, value)


@frappe.whitelist()
def migrate_yandex_users(dry_run: bool | str = False) -> dict[str, Any]:
    """Move legacy broker-linked users to local Keycloak credentials.

    The operation is idempotent: provisioning uses the Admin client's email
    upsert and the local social-login link is changed only after the required
    password action has been accepted by Keycloak.
    """
    _require_admin()
    dry_run_value = str(dry_run).strip().lower() in {"1", "true", "yes", "on"}
    client = None if dry_run_value else _get_keycloak_client()
    result: dict[str, Any] = {"migrated": 0, "skipped": 0, "errors": []}
    get_all = getattr(frappe, "get_all", None)
    if not callable(get_all):
        return result

    users = get_all(
        "User",
        fields=["name", "email", "first_name", "last_name"],
        limit_page_length=0,
    ) or []
    for user_row in users:
        user_name = str(user_row.get("name") if isinstance(user_row, dict) else getattr(user_row, "name", ""))
        email = str(user_row.get("email") if isinstance(user_row, dict) else getattr(user_row, "email", "") or user_name).strip().casefold()
        try:
            user_doc = frappe.get_doc("User", user_name)
            legacy_rows = _legacy_social_logins(user_doc)
            if not legacy_rows:
                result["skipped"] += 1
                continue
            if not email or "@" not in email:
                raise KeycloakProvisionError("Legacy user has no valid email")

            first_name = str(getattr(user_doc, "first_name", "") or "").strip()
            last_name = str(getattr(user_doc, "last_name", "") or "").strip()
            if dry_run_value:
                result.setdefault("planned", 0)
                result["planned"] += 1
                continue

            keycloak_id = client.upsert_user(email, first_name, last_name)
            client.send_password_setup(keycloak_id)
            for row in legacy_rows:
                _set_social_login_value(row, "provider", "keycloak")
                _set_social_login_value(row, "userid", keycloak_id)
            user_doc.flags.ignore_permissions = True
            save = getattr(user_doc, "save", None)
            if callable(save):
                save()
            result["migrated"] += 1
        except KeycloakProvisionError as error:
            result["errors"].append({"user": user_name or email, "error": str(error)[:240]})

    if result["errors"]:
        raise KeycloakProvisionError(
            f"Keycloak migration failed for {len(result['errors'])} user(s)"
        )
    return result
