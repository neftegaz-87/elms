"""DocType controller for ELMS Course."""

from frappe.model.document import Document

from elms.lms.custom_fields import validate_document_values


class ELMSCourse(Document):
	def validate(self) -> None:
		validate_document_values(self)
