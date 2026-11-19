"""Contract tests for parsed B2B admission confirmation."""

from __future__ import annotations

import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock, patch

import pytest
import frappe

for _frappe_name in ("get_doc", "get_all", "get_roles"):
	if not hasattr(frappe, _frappe_name):
		setattr(frappe, _frappe_name, Mock())
if not hasattr(frappe, "db"):
	frappe.db = SimpleNamespace(
		get_value=Mock(),
		savepoint=Mock(),
		rollback=Mock(),
		set_value=Mock(),
	)

# Keep the test boundary pointed at the schema package when the legacy
# ``elms.lms.api`` module shadows the sibling ``lms/api`` package directory.
_api_package = sys.modules.get("elms.lms.api")
_created_api_package = _api_package is None
if "frappe.model.document" not in sys.modules:
	_frappe_model = sys.modules.setdefault("frappe.model", ModuleType("frappe.model"))
	_frappe_document = ModuleType("frappe.model.document")
	_frappe_document.Document = object
	sys.modules["frappe.model.document"] = _frappe_document
	setattr(_frappe_model, "document", _frappe_document)
if _api_package is None:
	_api_package = ModuleType("elms.lms.api")
	_api_package.__path__ = [str(Path(__file__).resolve().parents[1] / "lms" / "api")]
	sys.modules["elms.lms.api"] = _api_package
elif not hasattr(_api_package, "__path__"):
	_api_package.__path__ = [str(Path(__file__).resolve().parents[1] / "lms" / "api")]

from elms.lms.api.schemas.admission import AdmissionConfirmRequest, parse_admission_request
from elms.lms.services.b2b_admission import (
	B2BAdmissionService,
	AdmissionPolicyError,
)

# The schema import above only needs a package-shaped parent.  Do not leave
# that lightweight shim in sys.modules: later tests exercise the real LMS API
# package and must not inherit a partially initialized module.
if _created_api_package and "elms.lms.api" in sys.modules:
	del sys.modules["elms.lms.api"]


def _row(row_id: str = "row-1", *, program: str = "Safety", training_kind: str = "DPO") -> SimpleNamespace:
	return SimpleNamespace(
		name=row_id,
		row_id=row_id,
		source_row_number=1,
		program=program,
		training_kind=training_kind,
		full_name="Иван Петров",
		first_name="Иван",
		last_name="Петров",
		middle_name="Иванович",
		phone="+79990000000",
		email=None,
	)


def _import_doc(*rows: SimpleNamespace, subscription_id: str | None = "SUB-1") -> SimpleNamespace:
	return SimpleNamespace(
		name="IMP-1",
		status="Parsed",
		organization="ORG-1",
		subscription_id=subscription_id,
		rows=list(rows),
	)


def _service() -> B2BAdmissionService:
	return B2BAdmissionService(user="admin@example.com", organization="ORG-1")


def _base_patches(import_doc: SimpleNamespace):
	course = {"name": "COURSE-1", "program": "safety", "training_kind": "dpo", "organization": None}
	batch = {"name": "BATCH-1", "course": "COURSE-1", "status": "Active"}
	subscription = {"name": "SUB-1", "subscription_id": "SUB-1", "status": "Active", "total_seats": 3, "seats_used": 1}
	return [
		patch("elms.lms.services.b2b_admission.frappe.get_doc", return_value=import_doc),
		patch(
			"elms.lms.services.b2b_admission.frappe.get_all",
			side_effect=[
				[subscription],
				[course],
				[batch],
			],
		),
		patch("elms.lms.services.b2b_admission.frappe.get_roles", return_value=["ELMS Company Admin"]),
		patch(
			"elms.lms.services.b2b_admission.frappe.db.get_value",
			side_effect=lambda *args, **kwargs: {"can_use_owner_catalog": 1, "can_publish_own": 1}
			if kwargs.get("as_dict")
			else "ORG-1",
		),
		patch("elms.lms.services.b2b_admission.frappe.db.savepoint"),
		patch("elms.lms.services.b2b_admission.frappe.db.rollback"),
		patch("elms.lms.services.b2b_admission.frappe.db.set_value"),
		patch("elms.lms.services.b2b_admission.reserve_seats", return_value=1),
	]


def test_request_accepts_only_parsed_import_selection() -> None:
	request = AdmissionConfirmRequest(import_id="IMP-1", row_ids='["row-1"]')

	assert request.import_id == "IMP-1"
	assert request.row_ids == ["row-1"]


def test_parse_admission_request_strips_frappe_transport_keys() -> None:
	request = parse_admission_request(
		payload='{"import_id":"IMP-1"}',
		cmd="elms.lms.api.admission.preview_admission_import",
		csrf_token="token",
	)

	assert request.import_id == "IMP-1"
	assert request.row_ids is None


def test_parse_admission_request_rejects_unknown_product_fields() -> None:
	with pytest.raises(Exception):
		parse_admission_request(import_id="IMP-1", unexpected_field="x")


def test_confirm_creates_active_enrollment_report_and_audit() -> None:
	import_doc = _import_doc(_row())
	patches = _base_patches(import_doc)
	with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patches[6], patches[7], patch(
		"elms.lms.services.b2b_admission.enroll_learner",
		return_value={"name": "ENR-1", "status": "Active", "learner": "USR-1"},
	) as enroll, patch(
		"elms.lms.services.b2b_admission._record_admission_audit",
	) as audit:
		result = _service().confirm("IMP-1")

	assert result.ok is True
	assert result.enrolled_count == 1
	assert result.remaining_seats == 1
	enroll.assert_called_once()
	audit.assert_called_once()


def test_confirm_rejects_quota_without_writing_or_enrolling() -> None:
	import_doc = _import_doc(_row(), _row("row-2"))
	patches = _base_patches(import_doc)
	patches[1] = patch(
		"elms.lms.services.b2b_admission.frappe.get_all",
		side_effect=[
			[{"name": "SUB-1", "subscription_id": "SUB-1", "status": "Active", "total_seats": 1, "seats_used": 1}],
			[{"name": "COURSE-1", "program": "safety", "training_kind": "dpo", "organization": None}],
			[{"name": "BATCH-1", "course": "COURSE-1", "status": "Active"}],
		],
	)
	with patches[0], patches[1], patches[2], patches[3], patch(
		"elms.lms.services.b2b_admission.enroll_learner",
	) as enroll, patch("elms.lms.services.b2b_admission._record_admission_audit") as audit:
		result = _service().confirm("IMP-1")

	assert result.ok is False
	assert result.errors[0].code == "QUOTA_EXCEEDED"
	assert result.enrolled_count == 0
	enroll.assert_not_called()
	audit.assert_not_called()


def test_confirm_rejects_missing_subscription_id() -> None:
	import_doc = _import_doc(_row(), subscription_id=None)
	patches = _base_patches(import_doc)
	with patches[0], patches[2], patches[3], patch(
		"elms.lms.services.b2b_admission.enroll_learner"
	) as enroll:
		result = _service().confirm("IMP-1")

	assert result.errors[0].code == "SUBSCRIPTION_REQUIRED"
	enroll.assert_not_called()


def test_confirm_rejects_ambiguous_subscription() -> None:
	import_doc = _import_doc(_row())
	with patch("elms.lms.services.b2b_admission.frappe.get_doc", return_value=import_doc), patch(
		"elms.lms.services.b2b_admission.frappe.get_roles", return_value=["ELMS Company Admin"]
	), patch(
		"elms.lms.services.b2b_admission.frappe.get_all",
		return_value=[
			{"name": "SUB-1", "subscription_id": "SUB-1", "status": "Active"},
			{"name": "SUB-2", "subscription_id": "SUB-1", "status": "Active"},
		],
	):
		result = _service().confirm("IMP-1")

	assert result.errors[0].code == "SUBSCRIPTION_AMBIGUOUS"


def test_confirm_rejects_inactive_subscription() -> None:
	import_doc = _import_doc(_row())
	with patch("elms.lms.services.b2b_admission.frappe.get_doc", return_value=import_doc), patch(
		"elms.lms.services.b2b_admission.frappe.get_roles", return_value=["ELMS Company Admin"]
	), patch("elms.lms.services.b2b_admission.frappe.get_all", return_value=[]):
		result = _service().confirm("IMP-1")

	assert result.errors[0].code == "SUBSCRIPTION_NOT_ACTIVE"


def test_confirm_rejects_owner_course_when_catalog_flag_is_disabled() -> None:
	import_doc = _import_doc(_row())
	patches = _base_patches(import_doc)
	patches[3] = patch(
		"elms.lms.services.b2b_admission.frappe.db.get_value",
		side_effect=lambda *args, **kwargs: {"can_use_owner_catalog": 0, "can_publish_own": 1}
		if kwargs.get("as_dict")
		else "ORG-1",
	)
	with patches[0], patches[1], patches[2], patches[3], patch(
		"elms.lms.services.b2b_admission.enroll_learner"
	) as enroll:
		result = _service().confirm("IMP-1")

	assert result.errors[0].code == "OWNER_CATALOG_FORBIDDEN"
	enroll.assert_not_called()


def test_confirm_reports_unknown_selected_row_without_writes() -> None:
	import_doc = _import_doc(_row())
	patches = _base_patches(import_doc)
	with patches[0], patches[1], patches[2], patches[3], patch(
		"elms.lms.services.b2b_admission.enroll_learner"
	) as enroll:
		result = _service().confirm("IMP-1", ["missing-row"])

	assert result.errors[0].code == "ROW_NOT_FOUND"
	enroll.assert_not_called()


def test_confirm_reports_ambiguous_course_before_writes() -> None:
	import_doc = _import_doc(_row())
	patches = _base_patches(import_doc)
	patches[1] = patch(
		"elms.lms.services.b2b_admission.frappe.get_all",
		side_effect=[
			[{"name": "SUB-1", "subscription_id": "SUB-1", "status": "Active", "total_seats": 3, "seats_used": 1}],
			[
				{"name": "COURSE-1", "program": "Safety", "training_kind": "DPO", "organization": None},
				{"name": "COURSE-2", "program": " safety ", "training_kind": "dpo", "organization": None},
			],
		],
	)
	with patches[0], patches[1], patches[2], patch(
		"elms.lms.services.b2b_admission.enroll_learner",
		return_value={"name": "ENR-1"},
	) as enroll:
		result = _service().confirm("IMP-1")

	assert result.ok is False
	assert result.errors[0].code == "COURSE_AMBIGUOUS"
	enroll.assert_not_called()


def test_confirm_reports_missing_course_before_writes() -> None:
	import_doc = _import_doc(_row())
	patches = _base_patches(import_doc)
	patches[1] = patch(
		"elms.lms.services.b2b_admission.frappe.get_all",
		side_effect=[
			[{"name": "SUB-1", "subscription_id": "SUB-1", "status": "Active", "total_seats": 3, "seats_used": 1}],
			[],
		],
	)
	with patches[0], patches[1], patches[2], patches[3], patch(
		"elms.lms.services.b2b_admission.enroll_learner"
	) as enroll:
		result = _service().confirm("IMP-1")

	assert result.errors[0].code == "COURSE_NOT_FOUND"
	enroll.assert_not_called()


def test_confirm_reports_ambiguous_batch_before_writes() -> None:
	import_doc = _import_doc(_row())
	patches = _base_patches(import_doc)
	patches[1] = patch(
		"elms.lms.services.b2b_admission.frappe.get_all",
		side_effect=[
			[{"name": "SUB-1", "subscription_id": "SUB-1", "status": "Active", "total_seats": 3, "seats_used": 1}],
			[{"name": "COURSE-1", "program": "safety", "training_kind": "dpo", "organization": None}],
			[
				{"name": "BATCH-1", "course": "COURSE-1", "status": "Active"},
				{"name": "BATCH-2", "course": "COURSE-1", "status": "Active"},
			],
		],
	)
	with patches[0], patches[1], patches[2], patches[3], patch(
		"elms.lms.services.b2b_admission.enroll_learner"
	) as enroll:
		result = _service().confirm("IMP-1")

	assert result.errors[0].code == "BATCH_AMBIGUOUS"
	enroll.assert_not_called()


def test_confirm_rolls_back_when_enrollment_fails_after_quota_reservation() -> None:
	import_doc = _import_doc(_row(), _row("row-2"))
	patches = _base_patches(import_doc)
	with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patches[6], patches[7], patch(
		"elms.lms.services.b2b_admission.enroll_learner",
		side_effect=[
			{"name": "ENR-1", "status": "Active"},
			AdmissionPolicyError("ENROLLMENT_REJECTED", "Строка отклонена", row_id="row-2"),
		],
	) as enroll, patch("elms.lms.services.b2b_admission._record_admission_audit") as audit, patch(
		"elms.lms.services.b2b_admission.frappe.db.rollback"
	) as rollback:
		result = _service().confirm("IMP-1")

	assert result.ok is False
	assert result.enrolled_count == 0
	assert result.errors[0].code == "ENROLLMENT_REJECTED"
	rollback.assert_called_once_with(save_point="b2b_admission_confirm")
	assert enroll.call_count == 2
	audit.assert_not_called()


def test_confirm_denies_import_from_another_organization() -> None:
	foreign_import = _import_doc(_row())
	foreign_import.organization = "ORG-OTHER"
	with patch("elms.lms.services.b2b_admission.frappe.get_doc", return_value=foreign_import), patch(
		"elms.lms.services.b2b_admission.frappe.get_roles", return_value=["ELMS Company Admin"]
	):
		with pytest.raises(AdmissionPolicyError) as exc_info:
			_service().confirm("IMP-1")

	assert exc_info.value.code == "ORGANIZATION_FORBIDDEN"
