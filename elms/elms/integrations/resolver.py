from __future__ import annotations

from typing import Any

import frappe

from elms.tenant import is_platform_admin, organizations_for_user


INTEGRATION_DOCTYPE = "ELMS Organization Integration"


class OrganizationIntegrationResolutionError(RuntimeError):
	pass


def _current_user() -> str:
	return str(getattr(getattr(frappe, "session", None), "user", "Guest") or "Guest")


def _password(doc: Any, fieldname: str) -> str:
	try:
		return str(doc.get_password(fieldname) or "").strip()
	except Exception:
		return str(getattr(doc, fieldname, "") or "").strip()


def resolve_organization(
	user: str | None = None,
	organization: str | None = None,
	*,
	allow_unscoped: bool = False,
) -> str | None:
	current = user or _current_user()
	requested = str(organization or "").strip()
	if requested:
		if is_platform_admin(current):
			return requested
		organizations = organizations_for_user(current)
		if requested not in organizations:
			raise OrganizationIntegrationResolutionError("Нет доступа к интеграции этой организации")
		return requested

	if is_platform_admin(current):
		return None
	organizations = organizations_for_user(current)
	if len(organizations) > 1:
		raise OrganizationIntegrationResolutionError("У пользователя несколько организаций: укажите организацию явно")
	if not organizations and current not in {"", "Guest"} and not allow_unscoped:
		raise OrganizationIntegrationResolutionError("У пользователя не определена организация")
	return organizations[0] if organizations else None


def get_organization_integration(
	integration_type: str,
	*,
	organization: str | None = None,
	user: str | None = None,
	allow_unscoped: bool = False,
) -> tuple[Any | None, str | None]:
	resolved = resolve_organization(user=user, organization=organization, allow_unscoped=allow_unscoped)
	if not resolved:
		return None, None
	name = frappe.db.exists(
		INTEGRATION_DOCTYPE,
		{"organization": resolved, "integration_type": integration_type, "enabled": 1},
	)
	if not name:
		return None, resolved
	return frappe.get_doc(INTEGRATION_DOCTYPE, name), resolved


def integration_secret(doc: Any, fieldname: str) -> str:
	return _password(doc, fieldname)
