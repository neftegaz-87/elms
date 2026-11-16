"""Optional field mapping for the Bitrix Lead boundary."""

try:
    from frappe.model.document import Document
except ImportError:
    class Document:  # pragma: no cover - unit-test shim
        pass


class ELMSApplicationSettings(Document):
    """Settings may customize source/field mapping, never application status."""

    pass
