"""DocType controller for ELMS Enrollment."""

import frappe
from frappe.model.document import Document


class ELMSEnrollment(Document):
	def before_insert(self):
		"""Keep quota enforcement on the server-side enrollment workflow."""
		if not getattr(self.flags, "from_lms_api", False):
			frappe.throw("Зачисление создаётся через действие «Оформить зачисление» в LMS")
