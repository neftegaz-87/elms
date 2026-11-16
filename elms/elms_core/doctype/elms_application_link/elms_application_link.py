"""Typed mirror of the Bitrix Lead created by a public application."""

import frappe

try:
    from frappe.model.document import Document
except ImportError:
    class Document:  # pragma: no cover - unit-test shim
        pass


class ELMSApplicationLink(Document):
    """Persist external identity and submission data, never a local status."""

    def validate(self) -> None:
        protected_fields = (
            "status",
            "".join(("mas", "ter", "_status")),
            "".join(("loc", "al_", "status")),
            "".join(("work", "flow_", "state")),
        )
        for fieldname in protected_fields:
            if getattr(self, fieldname, None):
                frappe.throw(
                    "Статус заявки читается из Bitrix и не изменяется в ELMS",
                    frappe.ValidationError,
                )
        if self.bitrix_entity != "lead":
            frappe.throw("Application Link must reference a Bitrix Lead", frappe.ValidationError)
        if self.application_kind not in ("individual", "legal"):
            frappe.throw("Application kind must be individual or legal", frappe.ValidationError)
        if not str(self.bitrix_id or "").isdigit():
            frappe.throw("Bitrix Lead id is required", frappe.ValidationError)
