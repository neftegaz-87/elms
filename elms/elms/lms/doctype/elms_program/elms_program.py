"""DocType controller for ELMS Program."""

from frappe.model.document import Document

from elms.lms.custom_fields import validate_document_values


class ELMSProgram(Document):
    """Published learning path that groups several ELMS courses."""

    def validate(self) -> None:
        validate_document_values(self)
