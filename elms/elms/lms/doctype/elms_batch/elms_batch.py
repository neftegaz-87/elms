"""DocType controller for ELMS Batch."""

import frappe
from frappe.model.document import Document

from elms.lms.custom_fields import validate_document_values


class ELMSBatch(Document):
	def validate(self) -> None:
		validate_document_values(self)
