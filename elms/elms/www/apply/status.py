"""Context for public application status tracking."""

from __future__ import annotations

import frappe

from elms.applications.api import get_application_status, refresh_application_status


def get_context(context: dict) -> dict:
    context.no_cache = 1
    reference = str(getattr(frappe, "form_dict", {}).get("ref", "") or "").strip()
    context.tracking_ref = reference
    context.application_status = None
    context.status_error = None
    if reference:
        try:
            refresh_requested = str(
                getattr(frappe, "form_dict", {}).get("refresh", "") or ""
            ).strip().lower() in {"1", "true", "yes"}
            if refresh_requested:
                context.application_status = refresh_application_status(
                    tracking_ref=reference
                )
            else:
                context.application_status = get_application_status(tracking_ref=reference)
        except Exception:
            context.status_error = "Заявка не найдена. Проверьте tracking ref."
    return context
