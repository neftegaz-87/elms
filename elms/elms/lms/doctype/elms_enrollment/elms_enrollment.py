"""DocType controller for ELMS Enrollment."""

from __future__ import annotations

import hashlib
import json
from typing import Any

import frappe
from frappe.model.document import Document


class ELMSEnrollment(Document):
	def before_validate(self):
		if self.course:
			self.course_name = frappe.db.get_value("ELMS Course", self.course, "course_name") or ""

	def before_insert(self):
		"""Keep quota enforcement on the server-side enrollment workflow."""
		if not getattr(self.flags, "from_lms_api", False):
			frappe.throw("Зачисление создаётся через действие «Оформить зачисление» в LMS")


def enroll_learner(
	*,
	learner_data: dict[str, Any],
	course: str,
	batch: str,
	subscription: str,
	source_import: str,
	quota_reserved: bool = False,
) -> dict[str, Any]:
	"""Create an Active enrollment after the admission service reserves quota."""
	if not quota_reserved:
		raise ValueError("Enrollment must be created through the quota admission boundary")
	user = _ensure_learner(learner_data, source_import)
	profile = _save_profile_snapshot(user, learner_data)
	organization = (
		frappe.db.get_value("ELMS Batch", batch, "organization")
		or frappe.db.get_value("ELMS Course", course, "organization")
	)
	if not organization:
		raise ValueError("Enrollment organization cannot be resolved from batch/course")
	enrollment = frappe.get_doc(
		{
			"doctype": "ELMS Enrollment",
			"organization": organization,
			"user": user,
			"course": course,
			"batch": batch,
			"subscription": subscription,
			"status": "Active",
			"source_import": source_import,
			"learner_profile_snapshot": json.dumps(profile, ensure_ascii=False, sort_keys=True),
		}
	)
	enrollment.flags.from_lms_api = True
	enrollment.insert(ignore_permissions=True)
	return {
		"name": enrollment.name,
		"status": enrollment.status,
		"learner": user,
		"user": user,
	}


def _ensure_learner(data: dict[str, Any], source_import: str) -> str:
	if data.get("user"):
		return str(data["user"])
	email = data.get("email") or _synthetic_email(data, source_import)
	existing = frappe.db.exists("User", email)
	if existing:
		return str(existing)
	user = frappe.get_doc(
		{
			"doctype": "User",
			"email": email,
			"first_name": data.get("first_name") or data.get("full_name") or email,
			"last_name": data.get("last_name") or "",
			"send_welcome_email": 0,
			"user_type": "Website User",
		}
	)
	user.insert(ignore_permissions=True)
	return str(user.name)


def _save_profile_snapshot(user: str, data: dict[str, Any]) -> dict[str, Any]:
	mapped = {
		"user": user,
		"email": data.get("email") or frappe.db.get_value("User", user, "email") or "",
		"fio_last_name": data.get("last_name") or "",
		"fio_first_name": data.get("first_name") or data.get("full_name") or "",
		"fio_middle_name": data.get("middle_name") or "",
		"phone": data.get("phone") or "",
		"snils": data.get("snils") or "",
		"passport_number": data.get("passport_number") or "",
		"education_level": data.get("education") or "",
		"profession": data.get("profession") or "",
	}
	profile_name = frappe.db.exists("ELMS Admission Profile", {"user": user})
	if profile_name:
		profile = frappe.get_doc("ELMS Admission Profile", profile_name)
		for field, value in mapped.items():
			if field == "user" or value in (None, ""):
				continue
			setattr(profile, field, value)
		profile.flags.from_b2b_admission = True
		profile.flags.ignore_mandatory = True
		profile.save(ignore_permissions=True)
	else:
		profile = frappe.get_doc({"doctype": "ELMS Admission Profile", **mapped})
		profile.flags.from_b2b_admission = True
		profile.flags.ignore_mandatory = True
		profile.insert(ignore_permissions=True)
	return {key: value for key, value in data.items() if value not in (None, "")}


def _synthetic_email(data: dict[str, Any], source_import: str) -> str:
	identity = "|".join(
		str(data.get(field) or "")
		for field in ("full_name", "phone", "passport_number", "snils")
	)
	digest = hashlib.sha256(f"{source_import}|{identity}".encode("utf-8")).hexdigest()[:20]
	return f"b2b-{digest}@learners.elms.invalid"
