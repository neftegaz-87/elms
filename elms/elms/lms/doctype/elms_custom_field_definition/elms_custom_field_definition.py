"""Controller for the org-scoped custom-field definition DocType."""

from frappe.model.document import Document

from elms.lms.custom_fields import validate_definition_document


class ELMSCustomFieldDefinition(Document):
    """Validate the schema before Frappe writes it."""

    def validate(self) -> None:
        validate_definition_document(self)
