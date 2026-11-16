"""Typed payloads for the B2C admission profile boundary."""

from __future__ import annotations

import base64
import binascii
import json
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AdmissionScan(BaseModel):
    """A document uploaded with the profile before payment."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    file_name: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1)
    content_type: str | None = Field(default=None, max_length=120)

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        encoded = value.split(",", 1)[1] if value.startswith("data:") and "," in value else value
        try:
            base64.b64decode(encoded, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise ValueError("Содержимое файла должно быть base64") from exc
        return value


class LearnerProfile(BaseModel):
    """The single typed SoT for learner admission data."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    fio_first_name: str = Field(min_length=1, max_length=80)
    fio_last_name: str = Field(min_length=1, max_length=80)
    fio_middle_name: str | None = Field(default=None, max_length=80)
    birth_date: str = Field(min_length=10, max_length=10)
    passport_series: str = Field(min_length=4, max_length=4)
    passport_number: str = Field(min_length=6, max_length=6)
    snils: str = Field(min_length=11, max_length=20)
    education_level: str = Field(min_length=1, max_length=80)
    profession: str = Field(min_length=1, max_length=160)
    phone: str = Field(min_length=5, max_length=40)
    consent_version: str = Field(min_length=1, max_length=80)
    passport_scan: AdmissionScan
    snils_scan: AdmissionScan
    education_doc_scan: AdmissionScan

    @field_validator("birth_date")
    @classmethod
    def validate_birth_date(cls, value: str) -> str:
        from datetime import date

        try:
            date.fromisoformat(value)
        except ValueError as exc:
            raise ValueError("Дата рождения должна быть в формате YYYY-MM-DD") from exc
        return value

    @field_validator("passport_series", "passport_number")
    @classmethod
    def validate_passport_digits(cls, value: str) -> str:
        if not value.isdigit():
            raise ValueError("Серия и номер паспорта должны содержать только цифры")
        return value

    @field_validator("snils")
    @classmethod
    def validate_snils(cls, value: str) -> str:
        digits = "".join(character for character in value if character.isdigit())
        if len(digits) != 11:
            raise ValueError("СНИЛС должен содержать 11 цифр")
        return value


def parse_learner_profile(payload: Any) -> LearnerProfile:
    """Parse the JSON boundary used by the Desk API."""

    value = payload
    if isinstance(payload, str):
        try:
            value = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise ValueError("Анкета должна быть JSON-объектом") from exc
    if not isinstance(value, dict):
        raise ValueError("Анкета должна быть JSON-объектом")
    return LearnerProfile.model_validate(value)
