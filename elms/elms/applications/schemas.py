"""Typed payloads for the public application forms."""

from __future__ import annotations

import json
import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
APPLICATION_KINDS = ("individual", "legal")


class ApplicationSubmitPayload(BaseModel):
    """Validated payload shared by the individual and legal forms."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    application_kind: Literal["individual", "legal"]
    fio: str | None = Field(default=None, max_length=160)
    email: str = Field(max_length=254)
    phone: str = Field(max_length=40)
    course: str | None = Field(default=None, max_length=140)
    company_name: str | None = Field(default=None, max_length=240)
    inn: str | None = Field(default=None, max_length=12)
    contact_fio: str | None = Field(default=None, max_length=160)
    course_ids: list[str] = Field(default_factory=list, max_length=50)
    comment: str | None = Field(default=None, max_length=2000)
    consent: bool
    honeypot: str = Field(default="", max_length=200, alias="website")

    @model_validator(mode="after")
    def validate_business_fields(self) -> "ApplicationSubmitPayload":
        if not EMAIL_PATTERN.fullmatch(self.email.lower()):
            raise ValueError("Укажите корректный email")
        if self.honeypot:
            raise ValueError("Недопустимое значение формы")
        if not self.consent:
            raise ValueError("Необходимо согласие на обработку персональных данных")

        if self.application_kind == "individual":
            if not self.fio:
                raise ValueError("Укажите ФИО")
            if not self.course:
                raise ValueError("Выберите курс")
            if self.course_ids:
                raise ValueError("Для физлица допустим один курс")
        else:
            if not self.company_name:
                raise ValueError("Укажите название компании")
            if not self.inn or not re.fullmatch(r"\d{10}|\d{12}", self.inn):
                raise ValueError("ИНН должен содержать 10 или 12 цифр")
            if not self.contact_fio:
                raise ValueError("Укажите ФИО контактного лица")
            if not self.course_ids:
                raise ValueError("Выберите хотя бы один курс")
            if self.course:
                raise ValueError("Для юрлица используйте список курсов")
            if len(set(self.course_ids)) != len(self.course_ids):
                raise ValueError("Курсы не должны повторяться")
        return self


def parse_application_payload(payload: Any) -> ApplicationSubmitPayload:
    """Parse the JSON argument received by a Frappe website method."""

    value: Any = payload
    if isinstance(payload, str):
        try:
            value = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise ValueError("Некорректный формат заявки") from exc
    if not isinstance(value, dict):
        raise ValueError("Заявка должна быть JSON-объектом")
    return ApplicationSubmitPayload.model_validate(value)
