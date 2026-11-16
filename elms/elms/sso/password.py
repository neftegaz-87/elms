"""First-login password boundary backed by Keycloak required actions."""

from __future__ import annotations

from typing import Any

import frappe

from elms.access.keycloak import (
    FIRST_LOGIN_PASSWORD_ATTRIBUTE,
    KeycloakAdminClient,
    KeycloakAdminSettings,
    KeycloakProvisionError,
)

if not hasattr(frappe, "whitelist"):
    def _whitelist(*args: Any, **kwargs: Any):
        def decorator(function: Any) -> Any:
            return function
        if args and callable(args[0]):
            return args[0]
        return decorator
    frappe.whitelist = _whitelist

try:
    from frappe import _
except (ImportError, AttributeError):
    def _(message: str, *args: Any) -> str:
        return message.format(*args) if args else message


PASSWORD_REQUIRED_ACTION = "UPDATE_PASSWORD"
MIN_PASSWORD_LENGTH = 8


def _current_user() -> str:
    user = str(getattr(getattr(frappe, "session", None), "user", "") or "").strip()
    if not user or user == "Guest":
        frappe.throw(_("Для смены пароля нужно войти в систему."), frappe.PermissionError)
    return user


def _keycloak_client() -> KeycloakAdminClient:
    return KeycloakAdminClient(KeycloakAdminSettings.from_env())


def _keycloak_user(client: KeycloakAdminClient, user: str) -> dict[str, Any]:
    email = user
    if "@" not in email and hasattr(frappe, "db"):
        email = str(frappe.db.get_value("User", user, "email") or user).strip()
    record = client.find_user(email)
    if not record or not record.get("id"):
        frappe.throw(_("Профиль пользователя в Keycloak не найден."), frappe.ValidationError)
    return record


def _required_actions(record: dict[str, Any]) -> list[str]:
    actions = record.get("requiredActions") or []
    if not isinstance(actions, list):
        frappe.throw(_("Keycloak вернул некорректное состояние аккаунта."), frappe.ValidationError)
    return [str(action).strip() for action in actions if str(action).strip()]


def _has_first_login_marker(record: dict[str, Any]) -> bool:
    attributes = record.get("attributes") or {}
    value = attributes.get(FIRST_LOGIN_PASSWORD_ATTRIBUTE) if isinstance(attributes, dict) else None
    if isinstance(value, list):
        return any(str(item).strip().casefold() in {"1", "true", "yes", "on"} for item in value)
    return str(value or "").strip().casefold() in {"1", "true", "yes", "on"}


@frappe.whitelist()
def get_password_change_state() -> dict[str, bool]:
    user = _current_user()
    try:
        record = _keycloak_user(_keycloak_client(), user)
    except KeycloakProvisionError:
        frappe.throw(_("Не удалось проверить состояние пароля в Keycloak."), frappe.ValidationError)
    return {
        "required": PASSWORD_REQUIRED_ACTION in _required_actions(record) or _has_first_login_marker(record)
    }


@frappe.whitelist(methods=["POST"])
def change_password(new_password: str | None = None, confirm_password: str | None = None) -> dict[str, bool]:
    user = _current_user()
    password = str(new_password or "")
    confirmation = str(confirm_password or "")
    if len(password) < MIN_PASSWORD_LENGTH:
        frappe.throw(
            _("Новый пароль должен содержать не менее {0} символов.").format(MIN_PASSWORD_LENGTH),
            frappe.ValidationError,
        )
    if password != confirmation:
        frappe.throw(_("Пароли не совпадают."), frappe.ValidationError)

    client = _keycloak_client()
    try:
        record = _keycloak_user(client, user)
        actions = _required_actions(record)
        if PASSWORD_REQUIRED_ACTION not in actions and not _has_first_login_marker(record):
            frappe.throw(_("Смена пароля при первом входе уже завершена."), frappe.ValidationError)
        client.set_password(str(record["id"]), password)
        client.update_required_actions(
            str(record["id"]),
            [action for action in actions if action != PASSWORD_REQUIRED_ACTION],
        )
        attributes = dict(record.get("attributes") or {})
        attributes.pop(FIRST_LOGIN_PASSWORD_ATTRIBUTE, None)
        client.update_attributes(str(record["id"]), attributes)
    except KeycloakProvisionError:
        frappe.throw(_("Не удалось изменить пароль в Keycloak."), frappe.ValidationError)
    return {"changed": True, "required": False}


__all__ = ["change_password", "get_password_change_state"]
