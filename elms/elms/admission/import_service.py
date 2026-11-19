"""Admission XLSX import orchestration: hash, grounded parse, DTO validation, and persistence."""

from __future__ import annotations

import base64
import hashlib
import json
import re
import zipfile
from dataclasses import dataclass
from datetime import date, timedelta
from io import BytesIO
from typing import Any, Callable, Iterable
from xml.etree import ElementTree

import frappe
from pydantic import ValidationError

from elms.ai import omniroute
from elms.admission.credentials import provision_credential

from .import_schemas import (
    SCHEMA_VERSION,
    XLSX_CONTENT_TYPES,
    AdmissionAIResponse,
    AdmissionHeader,
    AdmissionImportStatus,
    AdmissionRow,
    AdmissionRowPreview,
    AdmissionRowStatus,
)


if not hasattr(frappe, "ValidationError"):
    frappe.ValidationError = ValueError
if not hasattr(frappe, "PermissionError"):
    frappe.PermissionError = PermissionError


IMPORT_DOCTYPE = "ELMS Admission Import"
ROW_DOCTYPE = "ELMS Admission Import Row"
MAX_FILE_BYTES = 15 * 1024 * 1024
AI_TIMEOUT_SECONDS = 20
HEADER_LABELS = {
    "number": "№",
    "fio": "ФИО",
    "profession": "Профессия, занимаемая должность, разряд",
    "birth_date": "Дата рождения (дд.мм.гггг)",
    "snils": "СНИЛС",
    "education": "Информация об образовании",
    "phone": "Телефон",
    "contractor": "Контрагент",
    "program": "Программа",
    "training_kind": "Вид подготовки",
}


@dataclass(frozen=True)
class WorkbookDraft:
    """Raw workbook values sent to the grounded parser."""

    header: dict[str, str]
    rows: list[dict[str, Any]]
    sheet_name: str


@dataclass(frozen=True)
class RowValidationFailure:
    source_row_number: int
    values: dict[str, Any]
    errors: list[str]


@dataclass(frozen=True)
class ParseOutcome:
    status: AdmissionImportStatus
    header: AdmissionHeader
    rows: list[AdmissionRow]
    failures: list[RowValidationFailure]
    correlation_id: str | None = None
    error: str | None = None


def file_hash(content: bytes) -> str:
    """Return the stable SHA-256 identity used for idempotency."""

    return hashlib.sha256(content).hexdigest()


def _strip_data_url(value: str) -> str:
    return value.split(",", 1)[1] if value.startswith("data:") and "," in value else value


def decode_upload(content: bytes | str) -> bytes:
    if isinstance(content, bytes):
        return content
    try:
        return base64.b64decode(_strip_data_url(content), validate=True)
    except (ValueError, TypeError) as exc:
        raise ValueError("Файл должен быть передан как base64") from exc


def validate_upload(file_name: str, content_type: str | None, content: bytes) -> None:
    suffix = str(file_name or "").casefold().rsplit(".", 1)[-1]
    if suffix != "xlsx":
        raise ValueError("Поддерживается только канонический XLSX-файл")
    if content_type and content_type not in XLSX_CONTENT_TYPES and not content_type.endswith("+zip"):
        raise ValueError("Неверный MIME-тип XLSX-файла")
    if not content:
        raise ValueError("Файл не должен быть пустым")
    if len(content) > MAX_FILE_BYTES:
        raise ValueError("Файл превышает допустимый размер 15 МБ")


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _shared_strings(root: ElementTree.Element) -> list[str]:
    values: list[str] = []
    for item in root:
        if _local(item.tag) != "si":
            continue
        values.append("".join(node.text or "" for node in item.iter() if _local(node.tag) == "t"))
    return values


def _column_number(reference: str) -> int:
    letters = re.match(r"([A-Z]+)", reference.upper())
    if not letters:
        return 0
    result = 0
    for character in letters.group(1):
        result = result * 26 + ord(character) - ord("A") + 1
    return result


def _excel_date(value: str) -> str:
    try:
        serial = float(value)
    except ValueError:
        return value
    return (date(1899, 12, 30) + timedelta(days=serial)).isoformat()


def _cell_value(cell: ElementTree.Element, shared: list[str]) -> str:
    cell_type = cell.attrib.get("t", "")
    value_node = next((node for node in cell if _local(node.tag) == "v"), None)
    raw = "" if value_node is None else (value_node.text or "")
    if cell_type == "s":
        try:
            return shared[int(raw)]
        except (ValueError, IndexError):
            return ""
    if cell_type == "inlineStr":
        return "".join(node.text or "" for node in cell.iter() if _local(node.tag) == "t")
    if cell.attrib.get("r", "").startswith("E") and raw:
        return _excel_date(raw)
    return raw


def _parse_sheet(content: bytes) -> tuple[str, list[dict[int, str]]]:
    try:
        archive = zipfile.ZipFile(BytesIO(content))
        with archive:
            workbook = ElementTree.fromstring(archive.read("xl/workbook.xml"))
            rels = ElementTree.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
            shared = _shared_strings(ElementTree.fromstring(archive.read("xl/sharedStrings.xml"))) if "xl/sharedStrings.xml" in archive.namelist() else []
            first_sheet = next(node for node in workbook.iter() if _local(node.tag) == "sheet")
            relationship_id = first_sheet.attrib.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")
            relationship = next(
                node for node in rels.iter()
                if node.attrib.get("Id") == relationship_id
            )
            target = relationship.attrib["Target"].lstrip("/")
            if not target.startswith("xl/"):
                target = f"xl/{target}"
            sheet = ElementTree.fromstring(archive.read(target))
            rows: list[dict[int, str]] = []
            for row in sheet.iter():
                if _local(row.tag) != "row":
                    continue
                values: dict[int, str] = {}
                for cell in row:
                    if _local(cell.tag) != "c":
                        continue
                    values[_column_number(cell.attrib.get("r", ""))] = _cell_value(cell, shared).strip()
                rows.append(values)
            return str(first_sheet.attrib.get("name", "Sheet1")), rows
    except (KeyError, StopIteration, ValueError, zipfile.BadZipFile, ElementTree.ParseError) as exc:
        raise ValueError("Файл XLSX повреждён или не содержит рабочий лист") from exc


def _find_text(rows: Iterable[dict[int, str]], predicate: Callable[[str], bool]) -> str:
    for row in rows:
        for value in row.values():
            if value and predicate(value):
                return value
    return ""


def _header_from_sheet(rows: list[dict[int, str]]) -> dict[str, str]:
    organization_line = _find_text(rows, lambda value: "ИНН" in value and "предприятия" not in value)
    inn_match = re.search(r"ИНН\s*([0-9]{10,12})", organization_line)
    organization_name = re.sub(r",?\s*ИНН\s*[0-9]{10,12}", "", organization_line).strip(" ,")
    program_title = ""
    for row in rows:
        left = " ".join(value for column, value in row.items() if column <= 3)
        if "направляет для обучения" in left.casefold():
            program_title = row.get(4, "")
            break
    return {
        "organization_name": organization_name,
        "inn": inn_match.group(1) if inn_match else "",
        "program_title": program_title,
        "training_kind": "",
    }


def extract_workbook(content: bytes) -> WorkbookDraft:
    """Read the fixed columns from the fixture without treating them as validated rows."""

    sheet_name, sheet_rows = _parse_sheet(content)
    header_index = next(
        (index for index, row in enumerate(sheet_rows) if row.get(2) == HEADER_LABELS["number"] and row.get(3) == HEADER_LABELS["fio"]),
        None,
    )
    if header_index is None:
        raise ValueError("Не найдена каноническая строка заголовков XLSX")

    rows: list[dict[str, Any]] = []
    for row in sheet_rows[header_index + 1 :]:
        number = row.get(2, "")
        if not str(number).strip().isdigit():
            continue
        values = {
            "source_row_number": next((index + 1 for index, item in enumerate(sheet_rows) if item is row), 0),
            "fio": row.get(3, ""),
            "profession": row.get(4, ""),
            "birth_date": row.get(5, ""),
            "snils": row.get(6, ""),
            "education": row.get(7, ""),
            "phone": row.get(8, ""),
            "contractor": row.get(9, ""),
            "program": row.get(10, ""),
            "training_kind": row.get(11, ""),
            "email": row.get(12, ""),
        }
        if any(str(value).strip() for key, value in values.items() if key not in {"source_row_number"}):
            rows.append(values)
    return WorkbookDraft(header=_header_from_sheet(sheet_rows), rows=rows, sheet_name=sheet_name)


def parser_messages(workbook: WorkbookDraft) -> list[dict[str, str]]:
    """Build a bounded, grounded prompt; the workbook remains the only source."""

    payload = {
        "schema_version": SCHEMA_VERSION,
        "canonical_headers": HEADER_LABELS,
        "header": workbook.header,
        "rows": workbook.rows,
    }
    return [
        {
            "role": "system",
            "content": (
                "Ты возвращаешь только JSON для admission-xlsx-v1. Не придумывай значения. "
                "Сохрани source_row_number, а неизвестные поля оставь пустыми. Формат: "
                '{"schema_version":"admission-xlsx-v1","header":{...},"rows":[...]}.'
            ),
        },
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False, default=str)},
    ]


def parse_ai_response(content: str) -> AdmissionAIResponse:
    """Validate the provider envelope before any row is persisted."""

    text = content.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.IGNORECASE | re.DOTALL).strip()
    try:
        payload = json.loads(text)
        response = AdmissionAIResponse.model_validate(payload)
    except (json.JSONDecodeError, ValidationError, TypeError) as exc:
        raise ValueError("AI вернул JSON, не соответствующий admission-xlsx-v1") from exc
    if response.schema_version != SCHEMA_VERSION:
        raise ValueError(f"Неподдерживаемая версия схемы: {response.schema_version}")
    return response


def call_grounded_parser(workbook: WorkbookDraft, organization: str | None = None) -> tuple[AdmissionAIResponse, str]:
    config = omniroute.load_config(organization=organization)
    answer, correlation_id = omniroute.complete(
        parser_messages(workbook),
        model=config.default_model,
        config=config,
        timeout=AI_TIMEOUT_SECONDS,
    )
    return parse_ai_response(answer), correlation_id


def _row_number(values: dict[str, Any], fallback: int) -> int:
    value = values.get("source_row_number", values.get("row_number", fallback))
    try:
        return int(value)
    except (ValueError, TypeError):
        return fallback


def validate_provider_rows(response: AdmissionAIResponse) -> tuple[list[AdmissionRow], list[RowValidationFailure]]:
    valid: list[AdmissionRow] = []
    failures: list[RowValidationFailure] = []
    for index, raw in enumerate(response.rows, start=1):
        values = dict(raw)
        values["source_row_number"] = _row_number(values, index)
        try:
            valid.append(AdmissionRow.model_validate(values))
        except ValidationError as exc:
            failures.append(
                RowValidationFailure(
                    source_row_number=int(values["source_row_number"]),
                    values=values,
                    errors=["; ".join(str(item.get("msg", "Ошибка значения")) for item in exc.errors())],
                )
            )
    return valid, failures


def parse_workbook(
    content: bytes,
    *,
    organization: str | None = None,
    provider: Callable[[WorkbookDraft, str | None], tuple[AdmissionAIResponse, str]] = call_grounded_parser,
) -> ParseOutcome:
    """Parse a workbook fail-closed, retaining row-level errors for preview."""

    try:
        workbook = extract_workbook(content)
        response, correlation_id = provider(workbook, organization)
        header = AdmissionHeader.model_validate(response.header.model_dump())
        valid, failures = validate_provider_rows(response)
        if failures:
            return ParseOutcome(
                status=AdmissionImportStatus.FAILED,
                header=header,
                rows=valid,
                failures=failures,
                correlation_id=correlation_id,
                error="Одна или несколько строк не прошли проверку; исправьте ошибки и загрузите файл снова",
            )
        return ParseOutcome(
            status=AdmissionImportStatus.PARSED,
            header=header,
            rows=valid,
            failures=[],
            correlation_id=correlation_id,
        )
    except Exception as exc:
        return ParseOutcome(
            status=AdmissionImportStatus.FAILED,
            header=AdmissionHeader(),
            rows=[],
            failures=[],
            error=str(exc) or "Не удалось разобрать XLSX",
        )


def _existing_import(organization: str, digest: str) -> Any:
    return frappe.db.get_value(
        IMPORT_DOCTYPE,
        {"organization": organization, "file_hash": digest},
        ["name", "revision", "status"],
        as_dict=True,
    )


def _safe_date(value: Any) -> str:
    if isinstance(value, date):
        return value.isoformat()
    return str(value or "")


def _row_values(row: AdmissionRow, *, credential: str | None = None) -> dict[str, Any]:
    values = row.model_dump(mode="json")
    values["row_status"] = AdmissionRowStatus.VALID.value
    values["credential"] = credential or ""
    values["birth_date"] = _safe_date(row.birth_date)
    values["row_errors"] = ""
    return values


def _failure_values(failure: RowValidationFailure) -> dict[str, Any]:
    values = {
        "source_row_number": failure.source_row_number,
        "fio": failure.values.get("fio", ""),
        "profession": failure.values.get("profession", ""),
        "birth_date": str(failure.values.get("birth_date", "") or ""),
        "snils": str(failure.values.get("snils", "") or ""),
        "education": failure.values.get("education", ""),
        "phone": failure.values.get("phone", ""),
        "contractor": failure.values.get("contractor", ""),
        "program": failure.values.get("program", ""),
        "training_kind": failure.values.get("training_kind", ""),
        "email": failure.values.get("email", ""),
        "row_status": AdmissionRowStatus.INVALID.value,
        "credential": "",
        "row_errors": "\n".join(failure.errors),
    }
    return values


def _append_row(parent: Any, values: dict[str, Any]) -> None:
    append = getattr(parent, "append", None)
    if callable(append):
        append("rows", values)
        return
    child = frappe.get_doc({"doctype": ROW_DOCTYPE, "parent": parent.name, **values})
    child.insert(ignore_permissions=True)


def _parent_projection(doc: Any) -> dict[str, Any]:
    return {
        "name": str(getattr(doc, "name", "")),
        "status": str(getattr(doc, "status", "")),
        "subscription_id": str(getattr(doc, "subscription_id", "") or ""),
        "schema_version": str(getattr(doc, "schema_version", SCHEMA_VERSION)),
        "file_hash": str(getattr(doc, "file_hash", "")),
        "revision": int(getattr(doc, "revision", 1) or 1),
        "row_count": int(getattr(doc, "row_count", 0) or 0),
        "organization": str(getattr(doc, "organization", "")),
        "parse_error": str(getattr(doc, "parse_error", "") or ""),
    }


def persist_import(
    *,
    organization: str,
    file_name: str,
    content: bytes,
    new_revision: bool = False,
    subscription_id: str | None = None,
    provider: Callable[[WorkbookDraft, str | None], tuple[AdmissionAIResponse, str]] = call_grounded_parser,
) -> dict[str, Any]:
    digest = file_hash(content)
    existing = _existing_import(organization, digest)
    if existing and not new_revision:
        return _parent_projection(frappe.get_doc(IMPORT_DOCTYPE, existing["name"] if isinstance(existing, dict) else existing))
    revision = int((existing or {}).get("revision", 0) or 0) + 1 if isinstance(existing, dict) else 1
    parent = frappe.new_doc(IMPORT_DOCTYPE)
    parent.organization = organization
    if subscription_id:
        parent.subscription_id = subscription_id
    parent.source_file_name = file_name
    parent.file_hash = digest
    parent.schema_version = SCHEMA_VERSION
    parent.revision = revision
    parent.status = AdmissionImportStatus.DRAFT.value
    parent.insert(ignore_permissions=True)

    outcome = parse_workbook(content, organization=organization, provider=provider)
    parent.status = outcome.status.value
    parent.header_organization_name = outcome.header.organization_name
    parent.header_inn = outcome.header.inn
    parent.header_program_title = outcome.header.program_title
    parent.header_training_kind = outcome.header.training_kind
    parent.provider_correlation_id = outcome.correlation_id or ""
    parent.parse_error = outcome.error or ""
    parent.row_count = len(outcome.rows) + len(outcome.failures)
    for row in outcome.rows:
        credential = provision_credential(
            organization=organization,
            row=row,
            parent_import=str(parent.name),
        )
        _append_row(parent, _row_values(row, credential=(credential or {}).get("name")))
    for failure in outcome.failures:
        _append_row(parent, _failure_values(failure))
    parent.save(ignore_permissions=True)
    return _parent_projection(parent)


def _child_projection(row: Any) -> AdmissionRowPreview:
    errors = str(getattr(row, "row_errors", "") or "")
    return AdmissionRowPreview(
        name=str(getattr(row, "name", "")) or None,
        source_row_number=int(getattr(row, "source_row_number", 0) or 0),
        status=AdmissionRowStatus(str(getattr(row, "row_status", AdmissionRowStatus.INVALID.value))),
        fio=str(getattr(row, "fio", "") or ""),
        birth_date=getattr(row, "birth_date", None) or None,
        snils=str(getattr(row, "snils", "") or ""),
        profession=str(getattr(row, "profession", "") or ""),
        education=str(getattr(row, "education", "") or ""),
        phone=str(getattr(row, "phone", "") or ""),
        contractor=str(getattr(row, "contractor", "") or ""),
        program=str(getattr(row, "program", "") or ""),
        training_kind=str(getattr(row, "training_kind", "") or ""),
        email=str(getattr(row, "email", "") or "") or None,
        credential=str(getattr(row, "credential", "") or "") or None,
        errors=[item for item in errors.splitlines() if item],
    )


def inspect_import(import_name: str, *, page: int = 1, page_length: int = 50) -> dict[str, Any]:
    doc = frappe.get_doc(IMPORT_DOCTYPE, import_name)
    rows = list(getattr(doc, "rows", []) or [])
    start = max(page - 1, 0) * max(page_length, 1)
    end = start + max(page_length, 1)
    header = {
        "organization_name": str(getattr(doc, "header_organization_name", "") or ""),
        "inn": str(getattr(doc, "header_inn", "") or ""),
        "program_title": str(getattr(doc, "header_program_title", "") or ""),
        "training_kind": str(getattr(doc, "header_training_kind", "") or ""),
    }
    return {
        **_parent_projection(doc),
        "header": header,
        "rows": [row.model_dump(mode="json") for row in (_child_projection(item) for item in rows[start:end])],
        "total_rows": len(rows),
    }


def export_import(import_name: str) -> dict[str, Any]:
    doc = frappe.get_doc(IMPORT_DOCTYPE, import_name)
    if str(getattr(doc, "status", "")) != AdmissionImportStatus.PARSED.value:
        raise frappe.ValidationError("Экспорт доступен только для разобранного импорта")
    rows = [
        _child_projection(row).model_dump(mode="json")
        for row in list(getattr(doc, "rows", []) or [])
        if str(getattr(row, "row_status", "")) == AdmissionRowStatus.VALID.value
    ]
    return {
        "name": str(getattr(doc, "name", import_name)),
        "schema_version": str(getattr(doc, "schema_version", SCHEMA_VERSION)),
        "revision": int(getattr(doc, "revision", 1) or 1),
        "rows": rows,
    }
