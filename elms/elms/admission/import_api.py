"""Whitelisted, organization-scoped admission import endpoints."""

from __future__ import annotations

from typing import Any

import frappe

from elms.tenant import (
    ensure_platform_owner,
    is_company_admin,
    is_platform_admin,
    organizations_for_user,
)

from .credentials import reveal_credential as reveal_vault_credential
from .import_service import (
    IMPORT_DOCTYPE,
    decode_upload,
    export_import as export_import_projection,
    inspect_import as inspect_import_projection,
    persist_import,
    validate_upload,
)


if not hasattr(frappe, "PermissionError"):
    frappe.PermissionError = PermissionError
if not hasattr(frappe, "ValidationError"):
    frappe.ValidationError = ValueError


if not hasattr(frappe, "whitelist"):
    def _whitelist(*args: Any, **kwargs: Any):
        def decorator(function: Any) -> Any:
            return function
        if args and callable(args[0]):
            return args[0]
        return decorator
    frappe.whitelist = _whitelist


def _current_user() -> str:
    return str(getattr(getattr(frappe, "session", None), "user", "Guest") or "Guest")


def _roles(user: str) -> set[str]:
    get_roles = getattr(frappe, "get_roles", None)
    return set(get_roles(user) or []) if callable(get_roles) else set()


def _is_operations_user(user: str) -> bool:
    return "ELMS Operations User" in _roles(user)


def _resolve_organization(requested: str | None, *, write: bool = False) -> str:
    user = _current_user()
    if user == "Guest" or (not is_platform_admin(user) and not is_company_admin(user) and not _is_operations_user(user)):
        raise frappe.PermissionError("Для работы с импортом нужна роль администратора организации")

    if is_platform_admin(user):
        return str(requested or ensure_platform_owner())
    if is_company_admin(user):
        allowed = organizations_for_user(user)
        organization = str(requested or (allowed[0] if len(allowed) == 1 else ""))
        if not organization or organization not in allowed:
            raise frappe.PermissionError("Нет доступа к данным другой организации")
        return organization
    if write:
        raise frappe.PermissionError("Операционный пользователь может только просматривать импорт")
    return str(requested or ensure_platform_owner())


def _organization_for_import(import_name: str) -> str:
    doc = frappe.get_doc(IMPORT_DOCTYPE, import_name)
    return str(getattr(doc, "organization", "") or "")


@frappe.whitelist(methods=["POST"])
def upload_import(
    file_name: str,
    content: bytes | str,
    content_type: str | None = None,
    organization: str | None = None,
    new_revision: bool = False,
) -> dict[str, Any]:
    """Upload and parse one organization-scoped canonical workbook."""

    target_organization = _resolve_organization(organization, write=True)
    try:
        raw = decode_upload(content)
        validate_upload(file_name, content_type, raw)
    except ValueError as exc:
        raise frappe.ValidationError(str(exc)) from exc
    return persist_import(
        organization=target_organization,
        file_name=file_name,
        content=raw,
        new_revision=bool(new_revision),
    )


@frappe.whitelist(methods=["GET", "POST"])
def inspect_import(
	import_name: str,
	page: int | str = 1,
	page_length: int | str = 50,
) -> dict[str, Any]:
	"""Return a safe preview with row errors and credential references only."""

	target_organization = _resolve_organization(_organization_for_import(import_name))
	try:
		page_number = int(page)
		page_size = int(page_length)
	except (TypeError, ValueError) as exc:
		raise frappe.ValidationError("Параметры страницы preview должны быть целыми числами") from exc
	result = inspect_import_projection(import_name, page=page_number, page_length=page_size)
	if result.get("organization") != target_organization and not is_platform_admin(_current_user()):
		raise frappe.PermissionError("Нет доступа к данным другой организации")
	return result


@frappe.whitelist(methods=["GET", "POST"])
def export_import(import_name: str) -> dict[str, Any]:
    """Export validated structured rows for the authorized organization."""

    target_organization = _resolve_organization(_organization_for_import(import_name))
    result = export_import_projection(import_name)
    if result.get("organization") not in (None, "", target_organization) and not is_platform_admin(_current_user()):
        raise frappe.PermissionError("Нет доступа к данным другой организации")
    return result


@frappe.whitelist(methods=["POST"])
def reveal_credential(
    credential: str,
    reveal_intent: bool = False,
) -> dict[str, Any]:
    """Reveal a vault token only after an explicit, authorized admin action."""

    if not reveal_intent:
        raise frappe.ValidationError("Для раскрытия нужен явный признак reveal_intent")
    return reveal_vault_credential(credential, user=_current_user())
