"""Audit record for organization invitations."""

from frappe.model.document import Document


class ELMSInviteLog(Document):
    """Minimal audit record; credentials are intentionally not fields."""
