"""DocType controller for ELMS Course Progress."""

import frappe
from frappe.model.document import Document


class ELMSCourseProgress(Document):
	def before_validate(self):
		if self.enrollment:
			course = frappe.db.get_value("ELMS Enrollment", self.enrollment, "course")
			if not course:
				batch = frappe.db.get_value("ELMS Enrollment", self.enrollment, "batch")
				course = frappe.db.get_value("ELMS Batch", batch, "course") if batch else None
			self.course_name = frappe.db.get_value("ELMS Course", course, "course_name") if course else ""
