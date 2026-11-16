"""Bitrix Lead mapping for ELMS public applications."""

from __future__ import annotations

import json
from typing import Any

from scripts.bitrix.rest_client import BitrixRestError, post_json

from elms.integrations.bitrix_config import resolve_webhook_endpoint

from .schemas import ApplicationSubmitPayload


class BitrixLeadCreateError(RuntimeError):
    """Safe domain error for a failed Bitrix Lead creation."""


def _contact_fields(payload: ApplicationSubmitPayload) -> dict[str, Any]:
    name = payload.fio if payload.application_kind == "individual" else payload.contact_fio
    fields: dict[str, Any] = {
        "NAME": name,
        "EMAIL": [{"VALUE": payload.email, "VALUE_TYPE": "WORK"}],
        "PHONE": [{"VALUE": payload.phone, "VALUE_TYPE": "WORK"}],
        "SOURCE_ID": "WEB",
        "SOURCE_DESCRIPTION": "ELMS application form",
    }
    if payload.application_kind == "individual":
        fields["TITLE"] = f"Заявка на курс ELMS: {payload.course}"
        fields["COMMENTS"] = f"Тип заявки: individual; курс: {payload.course}"
    else:
        fields["TITLE"] = f"Заявка на сотрудничество ELMS: {payload.company_name}"
        fields["COMPANY_TITLE"] = payload.company_name
        fields["COMMENTS"] = (
            f"Тип заявки: legal; ИНН: {payload.inn}; курсы: {', '.join(payload.course_ids)}"
        )
        if payload.comment:
            fields["COMMENTS"] += f"; комментарий: {payload.comment}"
    return fields


def build_lead_params(payload: ApplicationSubmitPayload) -> dict[str, Any]:
    """Return the crm.lead.add argument envelope."""

    return {"fields": _contact_fields(payload)}


def _extract_lead_id(body: bytes) -> str:
    try:
        response = json.loads(body)
    except (TypeError, ValueError) as exc:
        raise BitrixLeadCreateError("Bitrix returned an invalid response") from exc

    result = response.get("result") if isinstance(response, dict) else None
    if isinstance(result, dict):
        result = result.get("ID") or result.get("id")
    lead_id = str(result or "").strip()
    if not lead_id or not lead_id.isdigit():
        raise BitrixLeadCreateError("Bitrix did not return a Lead id")
    return lead_id


def create_bitrix_lead(payload: ApplicationSubmitPayload) -> str:
    """Create a Lead through the single configured Bitrix REST transport."""

    try:
        endpoint = resolve_webhook_endpoint()
        body = post_json(endpoint, "crm.lead.add", build_lead_params(payload))
        return _extract_lead_id(body)
    except BitrixRestError as exc:
        raise BitrixLeadCreateError("Bitrix Lead creation failed") from exc
    except (TypeError, ValueError) as exc:
        raise BitrixLeadCreateError("Bitrix REST configuration is invalid") from exc
