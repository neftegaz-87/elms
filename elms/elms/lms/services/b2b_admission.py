"""Application service for atomic B2B parsed-import admission."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

import frappe

from elms.access.api import require_organization_mutation_access
from elms.lms.api.schemas.admission import AdmissionResult, AdmissionRowError
from elms.lms.doctype.elms_enrollment.elms_enrollment import enroll_learner
from elms.lms.doctype.elms_subscription.elms_subscription import QuotaExceededError, reserve_seats


IMPORT_DOCTYPE = "ELMS Admission Import"
SUBSCRIPTION_DOCTYPE = "ELMS Subscription"
COURSE_DOCTYPE = "ELMS Course"
BATCH_DOCTYPE = "ELMS Batch"
ORGANIZATION_DOCTYPE = "ELMS Organization"
COMPANY_ADMIN_ROLE = "ELMS Company Admin"
PARSED_STATUS = "parsed"


class AdmissionPolicyError(Exception):
	"""A fail-closed admission policy rejection."""

	def __init__(self, code: str, message: str, *, row_id: str | None = None) -> None:
		super().__init__(message)
		self.code = code
		self.message = message
		self.row_id = row_id


@dataclass(frozen=True)
class PreparedRow:
	row: Any
	row_id: str
	course: dict[str, Any]
	batch: dict[str, Any]


class B2BAdmissionService:
	"""Validate and commit one parsed import through the enrollment boundary."""

	def __init__(self, user: str | None = None, organization: str | None = None) -> None:
		self.user = user or frappe.session.user
		self.organization = organization

	def preview(self, import_id: str, row_ids: list[str] | None = None) -> AdmissionResult:
		"""Return the same validation report used by confirmation without writes."""
		import_doc = self._load_owned_parsed_import(import_id)
		subscription, subscription_error = self._resolve_subscription(import_doc)
		if subscription_error:
			return self._rejected(import_id, subscription_error)

		selected = self._select_rows(import_doc, row_ids)
		row_errors = self._row_selection_errors(import_id, import_doc, selected, row_ids)
		if row_errors:
			return self._rejected(import_id, row_errors, selected_count=len(selected))

		remaining = self._remaining_seats(subscription)
		prepared, errors = self._prepare_rows(selected)
		if not errors and len(prepared) > remaining:
			errors.append(
				AdmissionRowError(
					code="QUOTA_EXCEEDED",
					message=self._quota_message(remaining, len(prepared)),
				)
			)
		return self._result(
			import_id,
			import_doc,
			selected,
			prepared,
			errors,
			remaining_seats=remaining,
		)

	def confirm(self, import_id: str, row_ids: list[str] | None = None) -> AdmissionResult:
		"""Atomically confirm every valid selected row or return a typed report."""
		import_doc = self._load_owned_parsed_import(import_id)
		subscription, subscription_error = self._resolve_subscription(import_doc)
		if subscription_error:
			return self._rejected(import_id, subscription_error)

		selected = self._select_rows(import_doc, row_ids)
		row_errors = self._row_selection_errors(import_id, import_doc, selected, row_ids)
		if row_errors:
			return self._rejected(import_id, row_errors, selected_count=len(selected))

		prepared, errors = self._prepare_rows(selected)
		remaining = self._remaining_seats(subscription)
		if errors:
			return self._result(
				import_id,
				import_doc,
				selected,
				prepared,
				errors,
				remaining_seats=remaining,
			)
		if len(prepared) > remaining:
			return self._result(
				import_id,
				import_doc,
				selected,
				prepared,
				[AdmissionRowError(code="QUOTA_EXCEEDED", message=self._quota_message(remaining, len(prepared)))],
				remaining_seats=remaining,
			)

		savepoint = "b2b_admission_confirm"
		frappe.db.savepoint(savepoint)
		try:
			new_remaining = reserve_seats(subscription["name"], len(prepared))
			enrolled_rows: list[dict[str, Any]] = []
			for item in prepared:
				enrollment = enroll_learner(
					learner_data=self._profile_data(item.row),
					course=item.course["name"],
					batch=item.batch["name"],
					subscription=subscription["name"],
					source_import=import_id,
					quota_reserved=True,
				)
				enrolled_rows.append(
					{
						"row_id": item.row_id,
						"enrollment": self._value(enrollment, "name"),
						"status": self._value(enrollment, "status") or "Active",
					}
				)
			_record_admission_audit(
				actor=self.user,
				organization=self._actor_organization(),
				source_import=import_id,
				confirmed_count=len(enrolled_rows),
			)
			frappe.db.set_value(IMPORT_DOCTYPE, import_id, "status", "Confirmed")
		except AdmissionPolicyError as exc:
			frappe.db.rollback(save_point=savepoint)
			return self._rejected(
				import_id,
				[AdmissionRowError(code=exc.code, message=exc.message, row_id=exc.row_id)],
				selected_count=len(selected),
				remaining_seats=remaining,
			)
		except QuotaExceededError as exc:
			frappe.db.rollback(save_point=savepoint)
			return self._rejected(
				import_id,
				AdmissionRowError(code="QUOTA_EXCEEDED", message=str(exc)),
				selected_count=len(selected),
				remaining_seats=remaining,
			)
		except Exception:
			frappe.db.rollback(save_point=savepoint)
			raise

		return self._result(
			import_id,
			import_doc,
			selected,
			prepared,
			[],
			enrolled_rows=enrolled_rows,
			remaining_seats=new_remaining,
		)

	def _load_owned_parsed_import(self, import_id: str) -> Any:
		self._assert_company_admin()
		try:
			import_doc = frappe.get_doc(IMPORT_DOCTYPE, import_id)
		except Exception as exc:
			raise AdmissionPolicyError("IMPORT_NOT_FOUND", "Импорт не найден") from exc
		if str(self._value(import_doc, "status")).strip().casefold() != PARSED_STATUS:
			raise AdmissionPolicyError("IMPORT_NOT_PARSED", "Подтвердить можно только разобранный импорт")
		actor_org = self._actor_organization()
		if self._value(import_doc, "organization") != actor_org:
			raise AdmissionPolicyError(
				"ORGANIZATION_FORBIDDEN",
				"Импорт принадлежит другой организации",
			)
		return import_doc

	def _assert_company_admin(self) -> None:
		roles = set(frappe.get_roles(self.user))
		if COMPANY_ADMIN_ROLE not in roles or roles.intersection({"ELMS Admin", "ELMS Operations User", "Administrator", "System Manager"}):
			raise AdmissionPolicyError(
				"ACTOR_ROLE_FORBIDDEN",
				"Подтверждать B2B импорт может только Company Admin своей организации",
			)

	def _actor_organization(self) -> str:
		if self.organization:
			return self.organization
		organization = frappe.db.get_value(
			"ELMS Organization Member",
			{"user": self.user},
			"organization",
		)
		if not organization:
			raise AdmissionPolicyError(
				"ORGANIZATION_REQUIRED",
				"У Company Admin не определена активная организация",
			)
		self.organization = organization
		try:
			require_organization_mutation_access(organization, self.user)
		except frappe.PermissionError as exc:
			raise AdmissionPolicyError(
				"ORGANIZATION_FORBIDDEN",
				"Импорт принадлежит другой организации",
			) from exc
		return organization

	def _organization_flags(self) -> tuple[bool, bool]:
		flags = frappe.db.get_value(
			ORGANIZATION_DOCTYPE,
			self._actor_organization(),
			["can_use_owner_catalog", "can_publish_own"],
			as_dict=True,
		)
		return bool(self._value(flags, "can_use_owner_catalog")), bool(self._value(flags, "can_publish_own"))

	def _resolve_subscription(self, import_doc: Any) -> tuple[dict[str, Any] | None, AdmissionRowError | None]:
		subscription_id = self._value(import_doc, "subscription_id")
		if not subscription_id:
			return None, AdmissionRowError(code="SUBSCRIPTION_REQUIRED", message="В импорте не указана подписка")
		rows = frappe.get_all(
			SUBSCRIPTION_DOCTYPE,
			filters={"organization": self._actor_organization(), "status": "Active"},
			fields=["name", "organization", "status", "total_seats", "seats_used"],
			limit_page_length=0,
		)
		matches = [
			row
			for row in rows
			if self._value(row, "name") == subscription_id
			or self._value(row, "subscription_id") == subscription_id
		]
		if not matches:
			return None, AdmissionRowError(code="SUBSCRIPTION_NOT_ACTIVE", message="Нет активной подписки для импорта")
		if len(matches) > 1:
			return None, AdmissionRowError(code="SUBSCRIPTION_AMBIGUOUS", message="Для импорта найдено несколько активных подписок")
		return matches[0], None

	def _select_rows(self, import_doc: Any, row_ids: list[str] | None) -> list[Any]:
		rows = list(self._value(import_doc, "rows") or self._value(import_doc, "import_rows") or [])
		if not row_ids:
			return rows
		requested = set(row_ids)
		return [row for row in rows if self._row_id(row) in requested]

	def _row_selection_errors(
		self,
		import_id: str,
		import_doc: Any,
		selected: list[Any],
		row_ids: list[str] | None,
	) -> list[AdmissionRowError]:
		if not row_ids and not selected:
			return [AdmissionRowError(code="ROWS_NOT_FOUND", message=f"В импорте {import_id} нет выбранных строк")]
		if not row_ids:
			return []
		available = {
			self._row_id(row)
			for row in list(self._value(import_doc, "rows") or self._value(import_doc, "import_rows") or [])
		}
		return [
			AdmissionRowError(code="ROW_NOT_FOUND", message=f"Строка {row_id} не найдена в импорте", row_id=row_id)
			for row_id in row_ids
			if row_id not in available
		]

	def _prepare_rows(self, rows: list[Any]) -> tuple[list[PreparedRow], list[AdmissionRowError]]:
		prepared: list[PreparedRow] = []
		errors: list[AdmissionRowError] = []
		cache: dict[tuple[str, str], tuple[dict[str, Any], dict[str, Any]]] = {}
		for row in rows:
			row_id = self._row_id(row)
			try:
				pair = self._normalized_pair(row)
				if pair not in cache:
					cache[pair] = self._resolve_course_and_batch(*pair)
				course, batch = cache[pair]
				self._assert_catalog_access(course, row_id)
				prepared.append(PreparedRow(row=row, row_id=row_id, course=course, batch=batch))
			except AdmissionPolicyError as exc:
				errors.append(
					AdmissionRowError(
						code=exc.code,
						message=exc.message,
						row_id=exc.row_id or row_id,
						source_row_number=self._value(row, "source_row_number"),
					)
				)
		return prepared, errors

	def _resolve_course_and_batch(self, program: str, training_kind: str) -> tuple[dict[str, Any], dict[str, Any]]:
		courses = frappe.get_all(
			COURSE_DOCTYPE,
			filters={"status": "Active", "is_published": 1},
			fields=["name", "program", "training_kind", "organization", "course_name", "is_published"],
			limit_page_length=0,
		)
		matches = [
			course
			for course in courses
			if self._normalize(self._value(course, "program")) == program
			and self._normalize(self._value(course, "training_kind")) == training_kind
		]
		if not matches:
			raise AdmissionPolicyError("COURSE_NOT_FOUND", "Для строки не найден активный курс")
		if len(matches) > 1:
			raise AdmissionPolicyError("COURSE_AMBIGUOUS", "Для строки найдено несколько активных курсов")
		course = matches[0]
		batches = frappe.get_all(
			BATCH_DOCTYPE,
			filters={"status": "Active", "course": course["name"]},
			fields=["name", "course", "status"],
			limit_page_length=0,
		)
		if not batches:
			raise AdmissionPolicyError("BATCH_NOT_FOUND", "Для курса не найден активный поток")
		if len(batches) > 1:
			raise AdmissionPolicyError("BATCH_AMBIGUOUS", "Для курса найдено несколько активных потоков")
		return course, batches[0]

	def _assert_catalog_access(self, course: dict[str, Any], row_id: str) -> None:
		can_use_owner_catalog, can_publish_own = self._organization_flags()
		if self._value(course, "organization") == self._actor_organization():
			if not can_publish_own:
				raise AdmissionPolicyError(
					"OWN_CATALOG_FORBIDDEN",
					"Организации запрещено публиковать собственные курсы",
					row_id=row_id,
				)
		elif not can_use_owner_catalog:
			raise AdmissionPolicyError(
				"OWNER_CATALOG_FORBIDDEN",
				"Организации запрещено использовать каталог владельца",
				row_id=row_id,
			)

	def _profile_data(self, row: Any) -> dict[str, Any]:
		fields = (
			"full_name",
			"first_name",
			"last_name",
			"middle_name",
			"phone",
			"email",
			"snils",
			"passport_number",
			"education",
			"profession",
		)
		return {field: self._value(row, field) for field in fields if self._value(row, field) not in (None, "")}

	def _result(
		self,
		import_id: str,
		import_doc: Any,
		selected: list[Any],
		prepared: list[PreparedRow],
		errors: list[AdmissionRowError],
		*,
		enrolled_rows: list[dict[str, Any]] | None = None,
		remaining_seats: int | None = None,
	) -> AdmissionResult:
		return AdmissionResult(
			ok=not errors,
			status="confirmed" if enrolled_rows is not None and not errors else "rejected" if errors else "preview",
			import_id=import_id,
			organization=self._value(import_doc, "organization"),
			selected_count=len(selected),
			enrolled_count=len(enrolled_rows or []),
			remaining_seats=remaining_seats,
			rows=[self._row_report(row) for row in selected],
			enrolled_rows=enrolled_rows or [],
			errors=errors,
		)

	def _rejected(
		self,
		import_id: str,
		error: AdmissionRowError | list[AdmissionRowError],
		*,
		selected_count: int = 0,
		remaining_seats: int | None = None,
	) -> AdmissionResult:
		return AdmissionResult(
			ok=False,
			status="rejected",
			import_id=import_id,
			organization=self.organization,
			selected_count=selected_count,
			remaining_seats=remaining_seats,
			errors=error if isinstance(error, list) else [error],
		)

	def _remaining_seats(self, subscription: dict[str, Any]) -> int:
		return max(0, self._as_int(subscription.get("total_seats")) - self._as_int(subscription.get("seats_used")))

	@staticmethod
	def _quota_message(remaining: int, required: int) -> str:
		return f"Недостаточно мест: доступно {remaining}, требуется {required}"

	@staticmethod
	def _row_report(row: Any) -> dict[str, Any]:
		return {
			"row_id": B2BAdmissionService._row_id(row),
			"source_row_number": B2BAdmissionService._value(row, "source_row_number"),
			"program": B2BAdmissionService._value(row, "program"),
			"training_kind": B2BAdmissionService._value(row, "training_kind"),
			"full_name": B2BAdmissionService._value(row, "full_name"),
		}

	@staticmethod
	def _normalized_pair(row: Any) -> tuple[str, str]:
		program = B2BAdmissionService._normalize(B2BAdmissionService._value(row, "program"))
		training_kind = B2BAdmissionService._normalize(B2BAdmissionService._value(row, "training_kind"))
		if not program or not training_kind:
			raise AdmissionPolicyError("COURSE_FIELDS_REQUIRED", "В строке не указаны программа и вид обучения")
		return program, training_kind

	@staticmethod
	def _row_id(row: Any) -> str:
		return str(B2BAdmissionService._value(row, "row_id") or B2BAdmissionService._value(row, "name") or "")

	@staticmethod
	def _normalize(value: Any) -> str:
		return re.sub(r"\s+", " ", str(value or "").strip()).casefold()

	@staticmethod
	def _value(value: Any, key: str) -> Any:
		if value is None:
			return None
		if isinstance(value, dict):
			return value.get(key)
		return getattr(value, key, None)

	@staticmethod
	def _as_int(value: Any) -> int:
		try:
			return int(value or 0)
		except (TypeError, ValueError):
			return 0


def _record_admission_audit(
	*, actor: str, organization: str, source_import: str, confirmed_count: int
) -> None:
	"""Persist the confirmation trace inside the existing activity audit."""
	audit = frappe.get_doc(
		{
			"doctype": "ELMS User Activity",
			"user": actor,
			"organization": organization,
			"activity_type": f"B2B Admission Confirmed ({confirmed_count})",
			"timestamp": frappe.utils.now_datetime(),
			"reference_doctype": "ELMS Admission Import",
			"reference_name": source_import,
		}
	)
	audit.insert(ignore_permissions=True)
