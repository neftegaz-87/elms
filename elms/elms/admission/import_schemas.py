"""Typed contracts for the organization admission XLSX import boundary."""

from __future__ import annotations

import re
from datetime import date, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


SCHEMA_VERSION = "admission-xlsx-v1"
XLSX_CONTENT_TYPES = {
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/octet-stream",
}


class AdmissionImportStatus(str, Enum):
    """The only persisted parent import states."""

    DRAFT = "draft"
    PARSED = "parsed"
    FAILED = "failed"


class AdmissionRowStatus(str, Enum):
    """The only persisted child row states."""

    VALID = "valid"
    INVALID = "invalid"


class AdmissionHeader(BaseModel):
    """Header values extracted from the canonical application form."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    organization_name: str = Field(default="", max_length=255)
    inn: str = Field(default="", max_length=20)
    program_title: str = Field(default="", max_length=1000)
    training_kind: str = Field(default="", max_length=255)

    @field_validator("inn")
    @classmethod
    def normalize_inn(cls, value: str) -> str:
        return "".join(character for character in value if character.isdigit())


def _parse_date(value: Any) -> date | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value).strip()
    for pattern in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(text, pattern).date()
        except ValueError:
            continue
    raise ValueError("Дата рождения должна быть в формате YYYY-MM-DD или ДД.ММ.ГГГГ")


def _normalize_snils(value: Any) -> str:
    digits = "".join(character for character in str(value or "") if character.isdigit())
    if len(digits) != 11:
        raise ValueError("СНИЛС должен содержать 11 цифр")
    checksum = sum(int(digit) * (9 - index) for index, digit in enumerate(digits[:9]))
    if checksum < 100:
        expected = checksum
    elif checksum in (100, 101):
        expected = 0
    else:
        expected = checksum % 101
        if expected == 100:
            expected = 0
    if int(digits[9:]) != expected:
        raise ValueError("СНИЛС содержит неверную контрольную сумму")
    return digits


class AdmissionRow(BaseModel):
    """One validated learner row returned by the grounded AI parser."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    source_row_number: int = Field(ge=1)
    fio: str = Field(min_length=1, max_length=255)
    profession: str = Field(default="", max_length=255)
    birth_date: date | None = None
    snils: str
    education: str = Field(default="", max_length=255)
    phone: str = Field(default="", max_length=80)
    contractor: str = Field(default="", max_length=255)
    program: str = Field(default="", max_length=1000)
    training_kind: str = Field(default="", max_length=255)
    email: str | None = Field(default=None, max_length=255)

    @field_validator("birth_date", mode="before")
    @classmethod
    def validate_birth_date(cls, value: Any) -> date | None:
        return _parse_date(value)

    @field_validator("snils", mode="before")
    @classmethod
    def validate_snils(cls, value: Any) -> str:
        return _normalize_snils(value)

    @field_validator("email", mode="before")
    @classmethod
    def validate_email(cls, value: Any) -> str | None:
        text = str(value or "").strip().lower()
        if not text:
            return None
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", text):
            raise ValueError("Электронная почта имеет неверный формат")
        return text

    @property
    def full_name(self) -> str:
        """Compatibility projection used by preview and exports."""

        return self.fio


class AdmissionAIResponse(BaseModel):
    """Strict response envelope required from OmniRoute."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = Field(default=SCHEMA_VERSION)
    header: AdmissionHeader
    rows: list[dict[str, Any]] = Field(default_factory=list)


class AdmissionRowPreview(BaseModel):
    """Safe preview projection; secrets never belong in this model."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    source_row_number: int
    status: AdmissionRowStatus
    fio: str = ""
    birth_date: date | None = None
    snils: str = ""
    profession: str = ""
    education: str = ""
    phone: str = ""
    contractor: str = ""
    program: str = ""
    training_kind: str = ""
    email: str | None = None
    credential: str | None = None
    errors: list[str] = Field(default_factory=list)


def model_dump_jsonable(value: BaseModel) -> dict[str, Any]:
    """Return a JSON-safe model projection for Frappe responses."""

    return value.model_dump(mode="json")
