"""Whitelist methods for the Company Admin cabinet."""

from __future__ import annotations

from typing import Any

import frappe

from elms.cabinet.export import build_org_progress_export
from elms.cabinet.roster import build_org_roster


@frappe.whitelist()
def get_org_roster(
    organization: str | None = None,
    status_filter: str | None = None,
    page: int | str | None = 1,
    page_size: int | str | None = 50,
) -> dict[str, Any]:
    """Return a server-filtered roster for the caller's authorized organization."""
    return build_org_roster(
        organization=organization,
        status_filter=status_filter,
        page=page,
        page_size=page_size,
    )


@frappe.whitelist()
def export_org_progress(
    organization: str | None = None,
    status_filter: str | None = None,
) -> dict[str, Any]:
    """Return a server-generated CSV for the caller's authorized organization."""
    return build_org_progress_export(
        organization=organization,
        status_filter=status_filter,
    )
