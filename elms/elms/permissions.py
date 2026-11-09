"""ELMS access model helpers and the admin-safe Permission Manager bridge."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

import frappe
try:
    from frappe import _
except (ImportError, AttributeError):
    def _(text: str, *args: Any) -> str:
        return text.format(*args) if args else text
try:
    from frappe.core.page.permission_manager.permission_manager import not_allowed_in_permission_manager
    from frappe.exceptions import DoesNotExistError
    from frappe.modules.import_file import get_file_path, read_doc_from_file
    from frappe.permissions import (
        AUTOMATIC_ROLES,
        add_permission,
        get_all_perms,
        get_linked_doctypes,
        reset_perms,
        setup_custom_perms,
        update_permission_property,
    )
    from frappe.utils.user import get_users_with_role as _get_users_with_role
except ModuleNotFoundError:
    not_allowed_in_permission_manager = ["DocType", "Patch Log", "Module Def", "Transaction Log"]
    AUTOMATIC_ROLES = ("Guest", "All", "Desk User")
    DoesNotExistError = Exception
    get_file_path = read_doc_from_file = lambda *args, **kwargs: None
    add_permission = get_linked_doctypes = reset_perms = setup_custom_perms = update_permission_property = lambda *args, **kwargs: None
    get_all_perms = lambda role: []
    _get_users_with_role = lambda role: []

if not hasattr(frappe, "whitelist"):
    def _whitelist(*args, **kwargs):
        def decorator(function):
            return function
        if args and callable(args[0]):
            return args[0]
        return decorator
    frappe.whitelist = _whitelist


ELMS_ADMIN_ROLE = "ELMS Admin"
ELMS_LEARNER_ROLE = "ELMS Learner"
LEGACY_LEARNER_ROLE = "ELMS " + "LMS User"  # legacy migration only

ROLE_PROFILES: dict[str, tuple[str, ...]] = {
    "ELMS Learner Profile": ("Desk User", ELMS_LEARNER_ROLE),
    "ELMS Instructor Profile": ("Desk User", "ELMS Instructor"),
    "ELMS Methodologist Profile": ("Desk User", "ELMS Methodologist"),
    "ELMS Operations Profile": ("Desk User", "ELMS Operations User"),
    "ELMS Admin Profile": ("Desk User", ELMS_ADMIN_ROLE),
}

ROLE_DESCRIPTIONS: dict[str, str] = {
    ELMS_ADMIN_ROLE: "Полный продуктовый доступ: LMS, Operations, Review и Settings.",
    "ELMS Operations User": "Управление каталогом, потоками, квотами и зачислениями по рабочему процессу.",
    ELMS_LEARNER_ROLE: "Слушатель: доступ к назначенному обучению, своим зачислениям и прогрессу.",
    "ELMS Instructor": "Преподаватель или куратор: сопровождение потоков и проверка результатов обучения.",
    "ELMS Methodologist": "Методист: создание программ, курсов, уроков и банка вопросов.",
    "Desk User": "Техническая роль Frappe для входа в Desk; сама по себе не задаёт бизнес-права ELMS.",
    "System Manager": "Технический администратор Frappe: системные настройки и полная матрица прав.",
}

GROUP_POLICIES: dict[str, tuple[str, str]] = {
    "ELMS Learners": (
        "Адресация слушателей и учебные рассылки.",
        "Членство не назначает роль; доступ задаётся профилем пользователя и User Permission.",
    ),
    "ELMS Instructors": (
        "Адресация преподавателей и кураторов.",
        "Членство не выдаёт права на потоки или оценки автоматически.",
    ),
    "ELMS Methodologists": (
        "Адресация методистов и авторов контента.",
        "Членство не заменяет ELMS Methodologist Profile.",
    ),
    "ELMS Operations": (
        "Адресация операторов учебного процесса.",
        "Членство не выдаёт доступ к Operations или данным организаций.",
    ),
    "ELMS Administrators": (
        "Адресация продуктовых администраторов ELMS.",
        "Членство не делает пользователя System Manager; профиль назначается отдельно.",
    ),
}


def _has_access(user: str | None = None) -> bool:
    current_user = user or frappe.session.user
    return current_user == "Administrator" or bool(
        set(frappe.get_roles(current_user) or []).intersection({"System Manager", ELMS_ADMIN_ROLE})
    )


def _require_access() -> None:
    if not _has_access():
        frappe.throw(_("Access requires ELMS Admin or System Manager"), frappe.PermissionError)


def _ensure_write_access() -> None:
    _require_access()


@frappe.whitelist()
def get_role_profile_summary(role_profile: str) -> dict[str, Any]:
    """Return the effective roles and DocPerm rules shown on a Role Profile form."""

    _require_access()
    profile = frappe.get_doc("Role Profile", role_profile)
    roles = [row.role for row in profile.roles]
    permissions: dict[str, dict[str, Any]] = {}
    for role in roles:
        for permission in get_all_perms(role):
            if permission.get("permlevel", 0) != 0:
                continue
            doctype = permission.get("parent")
            if not doctype:
                continue
            entry = permissions.setdefault(
                doctype,
                {"doctype": doctype, "roles": [], "rights": set()},
            )
            entry["roles"].append(role)
            entry["rights"].update(
                right
                for right in ("read", "write", "create", "delete", "submit", "cancel", "amend")
                if permission.get(right)
            )

    users = frappe.get_all(
        "User",
        filters={"role_profile_name": role_profile},
        fields=["name", "full_name"],
        order_by="full_name asc",
    )
    result_permissions = []
    for entry in sorted(permissions.values(), key=lambda value: value["doctype"]):
        entry["rights"] = sorted(entry["rights"])
        entry["roles"] = sorted(set(entry["roles"]))
        result_permissions.append(entry)

    return {
        "name": profile.name,
        "roles": [{"name": role, "description": ROLE_DESCRIPTIONS.get(role, "Роль Frappe.")} for role in roles],
        "permissions": result_permissions,
        "users": users,
    }


@frappe.whitelist()
def get_group_policy(group: str) -> dict[str, str]:
    _require_access()
    purpose, limitation = GROUP_POLICIES.get(
        group,
        ("Организационная группа пользователей.", "Группа не выдаёт роли и не ограничивает записи."),
    )
    return {"group": group, "purpose": purpose, "limitation": limitation}


@frappe.whitelist()
def get_roles_and_doctypes():
    _require_access()
    active_domains = frappe.get_active_domains()
    doctypes = frappe.get_all(
        "DocType",
        filters={
            "istable": 0,
            "name": ("not in", ",".join(not_allowed_in_permission_manager)),
        },
        or_filters={"ifnull(restrict_to_domain, '')": "", "restrict_to_domain": ("in", active_domains)},
        fields=["name"],
    )
    restricted_roles = ["Administrator"]
    if frappe.session.user != "Administrator":
        custom_user_type_roles = frappe.get_all("User Type", filters={"is_standard": 0}, fields=["role"])
        restricted_roles.extend(row.role for row in custom_user_type_roles)
        restricted_roles.extend(AUTOMATIC_ROLES)
    roles = frappe.get_all(
        "Role",
        filters={"name": ("not in", restricted_roles), "disabled": 0},
        or_filters={"ifnull(restrict_to_domain, '')": "", "restrict_to_domain": ("in", active_domains)},
        fields=["name"],
    )
    return {
        "doctypes": sorted(
            [{"label": _(row.get("name")), "value": row.get("name")} for row in doctypes],
            key=lambda row: row["label"].casefold(),
        ),
        "roles": sorted(
            [{"label": _(row.get("name")), "value": row.get("name")} for row in roles],
            key=lambda row: row["label"].casefold(),
        ),
    }


@frappe.whitelist()
def get_permissions(doctype: str | None = None, role: str | None = None):
    _require_access()
    if role:
        out = get_all_perms(role)
        if doctype:
            out = [permission for permission in out if permission.parent == doctype]
    else:
        filters = {"parent": doctype}
        if frappe.session.user != "Administrator":
            custom_roles = frappe.get_all("Role", filters={"is_custom": 1}, pluck="name")
            filters["role"] = ["not in", custom_roles]
        out = frappe.get_all("Custom DocPerm", fields="*", filters=filters, order_by="permlevel")
        if not out:
            out = frappe.get_all("DocPerm", fields="*", filters=filters, order_by="permlevel")

    linked_doctypes: dict[str, Any] = {}
    for permission in out:
        if permission.parent not in linked_doctypes:
            try:
                linked_doctypes[permission.parent] = get_linked_doctypes(permission.parent)
            except DoesNotExistError:
                frappe.clear_last_message()
                continue
        permission.linked_doctypes = linked_doctypes[permission.parent]
        if meta := frappe.get_meta(permission.parent):
            permission.is_submittable = meta.is_submittable
            permission.in_create = meta.in_create
    return out


@frappe.whitelist()
def add(parent: str, role: str, permlevel: int):
    _ensure_write_access()
    add_permission(parent, role, permlevel)


@frappe.whitelist()
def update(doctype: str, role: str, permlevel: int, ptype: str, value: str | int | None = None, if_owner: str | int = 0):
    _ensure_write_access()
    if ptype == "report" and value == "1" and if_owner == "1":
        frappe.throw(_("Cannot set 'Report' permission if 'Only If Creator' permission is set"))
    result = update_permission_property(doctype, role, permlevel, ptype, value, if_owner=if_owner)
    if ptype == "if_owner" and value == "1":
        update_permission_property(doctype, role, permlevel, "report", "0", if_owner=value)
    frappe.db.after_commit.add(lambda: frappe.clear_cache(doctype=doctype))
    return "refresh" if result else None


@frappe.whitelist()
def remove(doctype: str, role: str, permlevel: int, if_owner: str | int = 0):
    _ensure_write_access()
    setup_custom_perms(doctype)
    frappe.db.delete("Custom DocPerm", {"parent": doctype, "role": role, "permlevel": permlevel, "if_owner": if_owner})
    if not frappe.get_all("Custom DocPerm", {"parent": doctype}):
        frappe.throw(_("There must be at least one permission rule."), title=_("Cannot Remove"))


@frappe.whitelist()
def reset(doctype: str):
    _ensure_write_access()
    reset_perms(doctype)
    frappe.clear_cache(doctype)


@frappe.whitelist()
def get_users_with_role(role: str):
    _require_access()
    return _get_users_with_role(role)


@frappe.whitelist()
def get_standard_permissions(doctype: str):
    _require_access()
    meta = frappe.get_meta(doctype)
    if meta.custom:
        doc = frappe.get_doc("DocType", doctype)
        return [permission.as_dict() for permission in doc.permissions]
    path = get_file_path(meta.module, "DocType", doctype)
    return read_doc_from_file(path).get("permissions")
