"""DocType controller for ELMS Lesson Progress."""

import frappe
from frappe.model.document import Document


class ELMSLessonProgress(Document):
	def before_validate(self):
		if self.course_progress:
			cp = frappe.db.get_value(
				"ELMS Course Progress",
				self.course_progress,
				["user", "course_name"],
				as_dict=True,
			)
			if cp:
				self.user = cp.get("user") or self.user
				self.course_name = cp.get("course_name") or self.course_name or ""
		if self.lesson:
			self.lesson_name = (
				frappe.db.get_value("ELMS Course Lesson", self.lesson, "lesson_name")
				or self.lesson_name
				or ""
			)
