"""Whitelisted API for Company Admin B2B admission confirmation."""

from __future__ import annotations

from typing import Any

import frappe

from elms.lms.api.schemas.admission import parse_admission_request
from elms.lms.services.b2b_admission import AdmissionPolicyError, B2BAdmissionService


@frappe.whitelist()
def preview_admission_import(
	import_id: str | None = None,
	row_ids: Any = None,
	payload: Any = None,
	**kwargs: Any,
) -> dict[str, Any]:
	"""Validate a parsed import and return preview data for the cabinet."""
	request = parse_admission_request(import_id=import_id, row_ids=row_ids, payload=payload, **kwargs)
	return _run(lambda: B2BAdmissionService().preview(request.import_id, request.row_ids), request.import_id)


@frappe.whitelist()
def confirm_admission_import(
	import_id: str | None = None,
	row_ids: Any = None,
	payload: Any = None,
	**kwargs: Any,
) -> dict[str, Any]:
	"""Confirm selected parsed rows through the atomic admission service."""
	request = parse_admission_request(import_id=import_id, row_ids=row_ids, payload=payload, **kwargs)
	return _run(lambda: B2BAdmissionService().confirm(request.import_id, request.row_ids), request.import_id)


def _run(operation, import_id: str) -> dict[str, Any]:
	try:
		return operation().as_dict()
	except AdmissionPolicyError as exc:
		if exc.code in {"ORGANIZATION_FORBIDDEN", "ACTOR_ROLE_FORBIDDEN", "ORGANIZATION_REQUIRED"}:
			frappe.throw(exc.message, exc=frappe.PermissionError)
		return {
			"ok": False,
			"status": "rejected",
			"import_id": import_id,
			"errors": [
				{
					"code": exc.code,
					"message": exc.message,
					"row_id": exc.row_id,
				}
			],
		}
