"""Synthetic admission identity and protected one-time invite-token vault."""

from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from typing import Any

import frappe

from elms.tenant import is_company_admin, is_platform_admin, organizations_for_user


CREDENTIAL_DOCTYPE = "ELMS Admission Credential"


if not hasattr(frappe, "PermissionError"):
    frappe.PermissionError = PermissionError
if not hasattr(frappe, "ValidationError"):
    frappe.ValidationError = ValueError


@dataclass(frozen=True)
class SyntheticIdentity:
    """Deterministic public identity plus the one-time secret shown to an admin."""

    login: str
    email: str
    invite_token: str


def _value(row: Any, fieldname: str, default: Any = "") -> Any:
    if isinstance(row, dict):
        return row.get(fieldname, default)
    return getattr(row, fieldname, default)


def synthetic_identity(organization: str, fio: str, snils: str) -> SyntheticIdentity:
    """Build a stable login/email and a fresh protected invite token."""

    seed = f"{organization.strip().casefold()}:{snils.strip()}".encode("utf-8")
    digest = hashlib.sha256(seed).hexdigest()[:16]
    login = f"admission-{digest}"
    return SyntheticIdentity(
        login=login,
        email=f"{login}@invite.elms.local",
        invite_token=secrets.token_urlsafe(32),
    )


def provision_credential(
    *,
    organization: str,
    row: Any,
    parent_import: str,
    user: str | None = None,
) -> dict[str, Any] | None:
    """Persist a protected credential only when the row has no email."""

    if _value(row, "email"):
        return None
    identity = synthetic_identity(
        organization,
        str(_value(row, "fio")),
        str(_value(row, "snils")),
    )
    doc = frappe.new_doc(CREDENTIAL_DOCTYPE)
    doc.organization = organization
    doc.parent_import = parent_import
    doc.login = identity.login
    doc.email = identity.email
    doc.invite_token = identity.invite_token
    doc.invite_token_revealed = 0
    doc.created_by = user or getattr(getattr(frappe, "session", None), "user", "Guest")
    doc.insert(ignore_permissions=True)
    return {
        "name": str(getattr(doc, "name", "")),
        "login": identity.login,
        "email": identity.email,
    }


def _authorized_for_organization(organization: str, user: str) -> bool:
    if is_platform_admin(user):
        return True
    if not (is_company_admin(user) or "ELMS Operations User" in set(frappe.get_roles(user) or [])):
        return False
    return organization in organizations_for_user(user)


def reveal_credential(credential_name: str, *, user: str | None = None) -> dict[str, Any]:
    """Reveal and immediately consume a protected invite token exactly once."""

    current = user or getattr(getattr(frappe, "session", None), "user", "Guest")
    doc = frappe.get_doc(CREDENTIAL_DOCTYPE, credential_name)
    organization = str(getattr(doc, "organization", "") or "")
    if not _authorized_for_organization(organization, current):
        raise frappe.PermissionError("Нет доступа к учётным данным другой организации")
    if int(getattr(doc, "invite_token_revealed", 0) or 0):
        raise frappe.ValidationError("Одноразовый invite-token уже был раскрыт")

    get_password = getattr(doc, "get_password", None)
    token = get_password("invite_token") if callable(get_password) else getattr(doc, "invite_token", "")
    if not token:
        raise frappe.ValidationError("Защищённый invite-token отсутствует")

    now = frappe.utils.now_datetime()
    doc.invite_token_revealed = 1
    doc.revealed_by = current
    doc.revealed_at = now
    doc.invite_token = ""
    doc.save(ignore_permissions=True)
    return {
        "name": str(getattr(doc, "name", credential_name)),
        "login": str(getattr(doc, "login", "")),
        "email": str(getattr(doc, "email", "")),
        "invite_token": str(token),
        "revealed_by": current,
        "revealed_at": now,
    }
