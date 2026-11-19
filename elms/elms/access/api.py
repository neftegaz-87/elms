"""Server-side B2B organization and scope operations."""

from __future__ import annotations

import json
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
ELMS_OPERATIONS_ROLE = "ELMS Operations User"
ELMS_COMPANY_ADMIN_ROLE = "ELMS Company Admin"
COMPANY_ADMIN_PROFILE = "ELMS Company Admin Profile"
DEFAULT_INVITE_PROFILE = "ELMS Learner Profile"
PLATFORM_VIEWER_ROLES = frozenset({ELMS_ADMIN_ROLE, ELMS_OPERATIONS_ROLE, "Administrator", "System Manager"})
ORGANIZATION_DOCTYPE = "ELMS Organization"
MEMBER_DOCTYPE = "ELMS Organization Member"
ORGANIZATION_ROLE_DOCTYPE = "ELMS Organization Role"
USER_PERMISSION_DOCTYPE = "User Permission"

COMPANY_MANAGED_PROFILES = (
    "ELMS Learner Profile",
    "ELMS Instructor Profile",
    "ELMS Methodologist Profile",
    COMPANY_ADMIN_PROFILE,
)
PLATFORM_MANAGED_PROFILES = COMPANY_MANAGED_PROFILES + (
    "ELMS Operations Profile",
    "ELMS Admin Profile",
)
PROFILE_ROLES = {
    "ELMS Learner Profile": ("Desk User", "ELMS Learner"),
    "ELMS Instructor Profile": ("Desk User", "ELMS Instructor"),
    "ELMS Methodologist Profile": ("Desk User", "ELMS Methodologist"),
    "ELMS Operations Profile": ("Desk User", "ELMS Operations User"),
    "ELMS Admin Profile": ("Desk User", ELMS_ADMIN_ROLE),
    COMPANY_ADMIN_PROFILE: ("Desk User", ELMS_COMPANY_ADMIN_ROLE),
}
COMPANY_CAPABILITIES = {
    "lms.catalog.manage": "Курсы и конструктор",
    "lms.process.manage": "Потоки, квоты и зачисления",
    "lms.progress.read": "Прогресс и активность слушателей",
    "lms.assessment.manage": "Тесты и аттестация",
}
CAPABILITY_ROLES = {
    "lms.catalog.manage": "ELMS Methodologist",
    "lms.process.manage": "ELMS Operations User",
    "lms.progress.read": "ELMS Instructor",
    "lms.assessment.manage": "ELMS Instructor",
}
MANAGED_ROLES = frozenset(
    role for profile in PROFILE_ROLES.values() for role in profile
) | {"ELMS LMS User"}


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


def _is_platform_viewer(user: str | None = None) -> bool:
    """Return whether the actor may read a selected organization platform-wide."""
    return bool(_roles(user).intersection(PLATFORM_VIEWER_ROLES))


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


def _organizations_for_user(user: str | None = None) -> list[str]:
    current = user or _current_user()
    get_all = getattr(frappe, "get_all", None)
    if not callable(get_all):
        return []
    rows = get_all(
        MEMBER_DOCTYPE,
        filters={"user": current},
        fields=["organization", "is_primary"],
        order_by="is_primary desc, modified asc",
        limit_page_length=0,
    ) or []
    organizations: list[str] = []
    for row in rows:
        value = str(row.get("organization") if isinstance(row, dict) else getattr(row, "organization", "") or "")
        if value and value not in organizations:
            organizations.append(value)
    return organizations


def _allowed_profiles(user: str | None = None) -> tuple[str, ...]:
    return PLATFORM_MANAGED_PROFILES if _is_admin(user) else COMPANY_MANAGED_PROFILES


def _capabilities(value: Any) -> list[str]:
    if isinstance(value, str):
        try:
            value = json.loads(value or "[]")
        except (TypeError, ValueError, json.JSONDecodeError) as error:
            _throw(f"Список возможностей должен быть JSON: {error}", frappe.ValidationError)
    if not isinstance(value, (list, tuple, set)):
        _throw("Список возможностей должен быть массивом", frappe.ValidationError)
    values = []
    for item in value:
        capability = str(item or "").strip()
        if capability not in COMPANY_CAPABILITIES:
            _throw("Недопустимая возможность внутренней роли", frappe.ValidationError)
        if capability not in values:
            values.append(capability)
    if not values:
        _throw("У внутренней роли должна быть хотя бы одна возможность", frappe.ValidationError)
    return values


def _role_row(row: Any) -> dict[str, Any]:
    value = row if isinstance(row, dict) else row.as_dict()
    raw = value.get("capabilities") or "[]"
    try:
        capabilities = _capabilities(raw)
    except Exception:
        capabilities = []
    return {
        "name": str(value.get("name") or ""),
        "organization": str(value.get("organization") or ""),
        "role_name": str(value.get("role_name") or ""),
        "description": str(value.get("description") or ""),
        "capabilities": capabilities,
        "enabled": bool(value.get("enabled", 1)),
    }


def _get_company_role(name: str, organization: str, require_enabled: bool = True) -> Any:
    role_name = _clean(name, "organization_role", 140)
    rows = frappe.get_all(
        ORGANIZATION_ROLE_DOCTYPE,
        filters={"name": role_name, "organization": organization},
        fields=["name"],
        limit_page_length=1,
    )
    if not rows:
        _throw("Внутренняя роль не найдена в этой организации", frappe.PermissionError)
    role = frappe.get_doc(ORGANIZATION_ROLE_DOCTYPE, rows[0].get("name"))
    if require_enabled and not getattr(role, "enabled", 1):
        _throw("Внутренняя роль отключена", frappe.ValidationError)
    return role


def _company_roles(organization: str) -> list[dict[str, Any]]:
    get_all = getattr(frappe, "get_all", None)
    if not callable(get_all):
        return []
    rows = get_all(
        ORGANIZATION_ROLE_DOCTYPE,
        filters={"organization": organization},
        fields=["name", "organization", "role_name", "description", "capabilities", "enabled"],
        order_by="role_name asc",
        limit_page_length=500,
    )
    return [_role_row(row) for row in rows]


def _require_company_admin(organization: str) -> str:
    selected = require_organization_access(organization)
    if not _is_admin() and ELMS_COMPANY_ADMIN_ROLE not in _roles():
        _throw("Управлять внутренними ролями может только Company Admin этой организации", frappe.PermissionError)
    return selected


def _set_capability_roles(user_doc: Any, organization_role: str, organization: str) -> None:
    role_doc = _get_company_role(organization_role, organization)
    required = {CAPABILITY_ROLES[key] for key in _capabilities(role_doc.capabilities) if key in CAPABILITY_ROLES}
    if not required:
        return
    current_rows = list(getattr(user_doc, "roles", []) or [])
    existing_names = {
        str(row.get("role", "") if isinstance(row, dict) else getattr(row, "role", "") or "")
        for row in current_rows
    }
    rows = current_rows + [{"role": role} for role in sorted(required) if role not in existing_names]
    setter = getattr(user_doc, "set", None)
    if callable(setter):
        setter("roles", rows)
    else:
        user_doc.roles = rows


def _validate_managed_profile(profile: str, user: str | None = None) -> str:
    value = str(profile or "").strip()
    if value not in PROFILE_ROLES:
        _throw("Недопустимый профиль доступа", frappe.ValidationError)
    if value not in _allowed_profiles(user):
        _throw("Этот профиль нельзя назначить внутри компании", frappe.PermissionError)
    return value


def _resolve_company_organization(organization: str | None = None) -> str:
    if organization and str(organization).strip():
        return require_organization_access(str(organization))
    organizations = _organizations_for_user()
    if len(organizations) == 1:
        return require_organization_access(organizations[0])
    if not organizations and not _is_admin():
        _throw("Пользователь не состоит ни в одной организации", frappe.PermissionError)
    _throw("Укажите организацию", frappe.ValidationError)
    raise AssertionError("frappe.throw must raise")


def _get_member(user: str, organization: str) -> Any:
    get_all = getattr(frappe, "get_all", None)
    rows = get_all(
        MEMBER_DOCTYPE,
        filters={"user": user, "organization": organization},
        fields=["name"],
        limit_page_length=1,
    ) if callable(get_all) else []
    if not rows:
        _throw("Пользователь не состоит в этой организации", frappe.PermissionError)
    member_name = rows[0].get("name") if isinstance(rows[0], dict) else getattr(rows[0], "name", "")
    return frappe.get_doc(MEMBER_DOCTYPE, member_name)


def _set_user_profile_roles(user_doc: Any, profile: str) -> None:
    required_roles = PROFILE_ROLES[profile]
    current_rows = list(getattr(user_doc, "roles", []) or [])
    preserved = []
    existing_names: set[str] = set()
    for row in current_rows:
        role = str(row.get("role", "") if isinstance(row, dict) else getattr(row, "role", "") or "")
        if role and role not in MANAGED_ROLES:
            preserved.append({"role": role})
            existing_names.add(role)
    rows = preserved + [{"role": role} for role in required_roles if role not in existing_names]
    setter = getattr(user_doc, "set", None)
    if callable(setter):
        setter("roles", rows)
    else:
        user_doc.roles = rows


@frappe.whitelist()
def get_company_access_context(organization: str | None = None) -> dict[str, Any]:
    """Return the organization selector and role profiles for the current user."""
    current = _current_user()
    platform_admin = _is_admin(current)
    platform_viewer = _is_platform_viewer(current)
    if platform_viewer:
        get_all = getattr(frappe, "get_all", None)
        rows = get_all(
            ORGANIZATION_DOCTYPE,
            fields=["name"],
            order_by="organization_name asc",
            limit_page_length=0,
        ) if callable(get_all) else []
        organizations = [
            str(row.get("name") if isinstance(row, dict) else getattr(row, "name", "") or "")
            for row in rows
        ]
    else:
        organizations = _organizations_for_user(current)
    selected = str(organization or "").strip()
    if selected:
        selected = require_organization_access(selected, current)
    elif len(organizations) == 1:
        selected = organizations[0]
    return {
        "organization": selected,
        "organizations": [value for value in organizations if value],
        "profiles": [] if platform_viewer else list(_allowed_profiles(current)),
        "capabilities": [] if platform_viewer else [
            {"value": key, "label": label} for key, label in COMPANY_CAPABILITIES.items()
        ],
        "company_roles": [] if platform_viewer else _company_roles(selected) if selected else [],
        "platform_admin": platform_admin,
        "platform_viewer": platform_viewer,
        "read_only": platform_viewer,
    }


@frappe.whitelist()
def get_organization_members(organization: str | None = None) -> dict[str, Any]:
    """List staff in one authorized organization; never accept a client roster."""
    organization_name = _resolve_company_organization(organization)
    get_all = getattr(frappe, "get_all", None)
    members = get_all(
        MEMBER_DOCTYPE,
        filters={"organization": organization_name},
		fields=["name", "user", "role_profile", "organization_role", "is_primary"],
        order_by="modified desc",
        limit_page_length=500,
    ) if callable(get_all) else []
    user_names = [str(row.get("user") if isinstance(row, dict) else getattr(row, "user", "") or "") for row in members]
    users = get_all(
        "User",
        filters={"name": ["in", user_names]},
        fields=["name", "email", "full_name", "first_name", "last_name", "enabled", "role_profile_name"],
        limit_page_length=500,
    ) if callable(get_all) and user_names else []
    users_by_name = {str(row.get("name") if isinstance(row, dict) else getattr(row, "name", "") or ""): row for row in users}
    result = []
    for member in members:
        member_row = member if isinstance(member, dict) else member.as_dict()
        user_name = str(member_row.get("user") or "")
        user_row = users_by_name.get(user_name, {})
        result.append(
            {
                "member": member_row.get("name"),
                "user": user_name,
                "email": user_row.get("email", user_name),
                "full_name": user_row.get("full_name") or " ".join(filter(None, [user_row.get("first_name"), user_row.get("last_name")])),
                "enabled": bool(user_row.get("enabled")),
                "role_profile": member_row.get("role_profile") or user_row.get("role_profile_name") or DEFAULT_INVITE_PROFILE,
                "organization_role": member_row.get("organization_role") or "",
            }
        )
    return {"organization": organization_name, "members": result}


@frappe.whitelist()
def update_organization_member(user: str, organization: str, role_profile: str, organization_role: str | None = None) -> dict[str, str]:
    """Change only a member's approved product profile inside an organization."""
    organization_name = require_organization_access(organization)
    profile = _validate_managed_profile(role_profile)
    user_name = _clean(user, "user", 180).casefold()
    member = _get_member(user_name, organization_name)
    if not _is_admin() and _roles(user_name).intersection({ELMS_ADMIN_ROLE, "System Manager"}):
        _throw("Нельзя изменять глобального администратора из компании", frappe.PermissionError)
    user_doc = frappe.get_doc("User", user_name)
    user_doc.role_profile_name = profile
    _set_user_profile_roles(user_doc, profile)
    user_doc.flags.ignore_permissions = True
    user_doc.save()
    member.role_profile = profile
    if organization_role is not None:
        role_name = str(organization_role or "").strip()
        if role_name:
            _get_company_role(role_name, organization_name)
            member.organization_role = role_name
            _set_capability_roles(user_doc, role_name, organization_name)
        else:
            member.organization_role = ""
    member.flags.ignore_permissions = True
    member.save()
    return {
        "user": user_name,
        "organization": organization_name,
        "role_profile": profile,
        "organization_role": str(getattr(member, "organization_role", "") or ""),
    }


@frappe.whitelist()
def disable_organization_member(user: str, organization: str) -> dict[str, str]:
    """Disable a staff account after verifying organization membership."""
    organization_name = require_organization_access(organization)
    user_name = _clean(user, "user", 180).casefold()
    _get_member(user_name, organization_name)
    if not _is_admin() and _roles(user_name).intersection({ELMS_ADMIN_ROLE, "System Manager"}):
        _throw("Нельзя отключить глобального администратора из компании", frappe.PermissionError)
    user_doc = frappe.get_doc("User", user_name)
    user_doc.enabled = 0
    user_doc.flags.ignore_permissions = True
    user_doc.save()
    return {"user": user_name, "organization": organization_name, "status": "disabled"}


@frappe.whitelist()
def create_organization_role(
    organization: str,
    role_name: str,
    description: str | None = None,
    capabilities: Any = None,
) -> dict[str, Any]:
    """Create a company-scoped capability role without creating a global Frappe Role."""
    organization_name = _require_company_admin(organization)
    name = _clean(role_name, "role_name", 120)
    selected = _capabilities(capabilities or [])
    if frappe.db.exists(ORGANIZATION_ROLE_DOCTYPE, {"organization": organization_name, "role_name": name}):
        _throw("В этой организации уже есть роль с таким названием", frappe.ValidationError)
    role = frappe.get_doc(
        {
            "doctype": ORGANIZATION_ROLE_DOCTYPE,
            "organization": organization_name,
            "role_name": name,
            "description": str(description or "").strip()[:500],
            "capabilities": json.dumps(selected, ensure_ascii=False),
            "enabled": 1,
        }
    )
    role.flags.ignore_permissions = True
    role.insert(ignore_permissions=True)
    return _role_row(role)


@frappe.whitelist()
def update_organization_role(
    name: str,
    organization: str,
    role_name: str,
    description: str | None = None,
    capabilities: Any = None,
    enabled: Any = 1,
) -> dict[str, Any]:
    organization_name = _require_company_admin(organization)
    role = _get_company_role(name, organization_name, require_enabled=False)
    new_name = _clean(role_name, "role_name", 120)
    selected = _capabilities(capabilities or [])
    duplicate = frappe.db.exists(
        ORGANIZATION_ROLE_DOCTYPE,
        {"organization": organization_name, "role_name": new_name, "name": ["!=", role.name]},
    )
    if duplicate:
        _throw("В этой организации уже есть роль с таким названием", frappe.ValidationError)
    role.role_name = new_name
    role.description = str(description or "").strip()[:500]
    role.capabilities = json.dumps(selected, ensure_ascii=False)
    role.enabled = int(bool(enabled))
    role.flags.ignore_permissions = True
    role.save(ignore_permissions=True)
    return _role_row(role)


@frappe.whitelist()
def delete_organization_role(name: str, organization: str) -> dict[str, str]:
    organization_name = _require_company_admin(organization)
    role = _get_company_role(name, organization_name)
    if frappe.db.exists(MEMBER_DOCTYPE, {"organization": organization_name, "organization_role": role.name}):
        _throw("Сначала снимите эту роль с сотрудников организации", frappe.ValidationError)
    role.delete(ignore_permissions=True)
    return {"organization": organization_name, "name": role.name, "status": "deleted"}


def require_organization_access(organization: str, user: str | None = None) -> str:
    """Enforce platform read access or explicit Company Admin membership."""
    organization_name = _clean(organization, "organization")
    current = user or _current_user()
    is_company_admin = ELMS_COMPANY_ADMIN_ROLE in _roles(current)
    if _is_platform_viewer(current) or (
        is_company_admin and organization_membership_exists(current, organization_name)
    ):
        return organization_name
    _throw("Нет доступа к этой организации", frappe.PermissionError)
    raise AssertionError("frappe.throw must raise")


def require_organization_mutation_access(organization: str, user: str | None = None) -> str:
    """Require explicit Company Admin membership for company-scoped writes."""
    organization_name = _clean(organization, "organization")
    current = user or _current_user()
    if ELMS_COMPANY_ADMIN_ROLE in _roles(current) and organization_membership_exists(current, organization_name):
        return organization_name
    _throw(
        "Изменять данные организации может только Company Admin этой организации",
        frappe.PermissionError,
    )
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
    else:
        _ensure_membership_and_scope(user_name, organization_name, COMPANY_ADMIN_PROFILE)
        return {
            "user": user_name,
            "organization": organization_name,
            "role_profile": COMPANY_ADMIN_PROFILE,
        }
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
    _set_user_profile_roles(user_doc, role_profile)
    user_doc.flags.ignore_permissions = True
    if created:
        _insert(user_doc)
    elif callable(getattr(user_doc, "save", None)):
        user_doc.save()
    return user_doc, created


def _ensure_membership_and_scope(user: str, organization: str, role_profile: str, organization_role: str = "") -> None:
    if not organization_membership_exists(user, organization):
        membership = _new_doc(
            {
                "doctype": MEMBER_DOCTYPE,
                "user": user,
                "organization": organization,
                "role_profile": role_profile,
                "organization_role": organization_role,
                "is_primary": 1,
            }
        )
        _insert(membership)
    else:
        get_all = getattr(frappe, "get_all", None)
        rows = get_all(
            MEMBER_DOCTYPE,
            filters={"user": user, "organization": organization},
            fields=["name", "role_profile"],
            limit_page_length=1,
        ) if callable(get_all) else []
        if rows:
            row = rows[0] if isinstance(rows[0], dict) else rows[0].as_dict()
            if row.get("role_profile") != role_profile or organization_role:
                membership = frappe.get_doc(MEMBER_DOCTYPE, row.get("name"))
                membership.role_profile = role_profile
                if organization_role:
                    membership.organization_role = organization_role
                membership.flags.ignore_permissions = True
                membership.save()
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
    organization_role: str | None = None,
) -> dict[str, Any]:
    """Provision a user in Frappe and Keycloak for an authorized organization."""
    email_value = _clean(email, "email", 180).casefold()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email_value):
        _throw("Укажите корректный email", frappe.ValidationError)
    first_name_value = _clean(first_name, "first_name", 120)
    last_name_value = _clean(last_name, "last_name", 120)
    organization_value = require_organization_mutation_access(organization)
    profile = _validate_managed_profile(role_profile or DEFAULT_INVITE_PROFILE)
    role_name = str(organization_role or "").strip()
    if role_name:
        _get_company_role(role_name, organization_value)

    user_doc, created = _create_or_get_frappe_user(
        email_value, first_name_value, last_name_value, profile
    )
    user_name = str(getattr(user_doc, "name", email_value))
    if role_name:
        _ensure_membership_and_scope(user_name, organization_value, profile, role_name)
    else:
        _ensure_membership_and_scope(user_name, organization_value, profile)
    if role_name:
        _set_capability_roles(user_doc, role_name, organization_value)
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
        "user": user_name,
        "organization": organization_value,
        "organization_role": role_name,
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
