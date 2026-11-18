"""Typed request and report models for the B2B admission boundary."""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AdmissionConfirmRequest(BaseModel):
    """Validated payload accepted by preview and confirmation endpoints."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    import_id: str = Field(min_length=1, max_length=140)
    row_ids: list[str] | None = None

    @field_validator("row_ids", mode="before")
    @classmethod
    def parse_row_ids(cls, value: Any) -> list[str] | None:
        if value in (None, "", []):
            return None
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except json.JSONDecodeError as exc:
                raise ValueError("row_ids must be a JSON array") from exc
        if not isinstance(value, list):
            raise ValueError("row_ids must be a list")
        result = [str(item).strip() for item in value if str(item).strip()]
        if len(result) != len(set(result)):
            raise ValueError("row_ids must not contain duplicates")
        return result or None


class AdmissionRowError(BaseModel):
    """One typed row or batch rejection returned to the cabinet."""

    model_config = ConfigDict(extra="forbid")

    code: str
    message: str
    row_id: str | None = None
    source_row_number: int | None = None


class AdmissionResult(BaseModel):
    """Stable JSON shape for preview, success, and rejected confirmation."""

    model_config = ConfigDict(extra="allow")

    ok: bool
    status: str
    import_id: str
    organization: str | None = None
    selected_count: int = 0
    enrolled_count: int = 0
    remaining_seats: int | None = None
    rows: list[dict[str, Any]] = Field(default_factory=list)
    enrolled_rows: list[dict[str, Any]] = Field(default_factory=list)
    errors: list[AdmissionRowError] = Field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


def parse_admission_request(
    import_id: str | None = None,
    row_ids: Any = None,
    payload: Any = None,
    **kwargs: Any,
) -> AdmissionConfirmRequest:
    """Accept Frappe's JSON/string payload variants without widening the model."""

    value: Any = payload
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError as exc:
            raise ValueError("Admission payload must be a JSON object") from exc
    if value is None:
        value = {}
    if not isinstance(value, dict):
        raise ValueError("Admission payload must be a JSON object")
    normalized = dict(value)
    normalized.update(kwargs)
    if import_id is not None:
        normalized["import_id"] = import_id
    if row_ids is not None:
        normalized["row_ids"] = row_ids
    if "import" in normalized and "import_id" not in normalized:
        normalized["import_id"] = normalized.pop("import")
    if "admission_import" in normalized and "import_id" not in normalized:
        normalized["import_id"] = normalized.pop("admission_import")
    return AdmissionConfirmRequest.model_validate(normalized)
