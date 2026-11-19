"""The single schema, validation, and inheritance boundary for ELMS fields."""

from __future__ import annotations

import json
import math
import re
from collections.abc import Iterable, Mapping
from datetime import date
from typing import Any

import frappe

from elms.access.api import organization_membership_exists, require_organization_access


if not hasattr(frappe, "ValidationError"):
    frappe.ValidationError = ValueError
if not hasattr(frappe, "PermissionError"):
    frappe.PermissionError = PermissionError
if not hasattr(frappe, "DoesNotExistError"):
    frappe.DoesNotExistError = LookupError
if not hasattr(frappe, "throw"):
    def _throw(message: str, exception: type[Exception] = Exception, *args: Any, **kwargs: Any) -> None:
        raise exception(message)

    frappe.throw = _throw


SCHEMA_VERSION = 1
DEFINITION_DOCTYPE = "ELMS Custom Field Definition"
CUSTOM_VALUES_FIELD = "custom_field_values"
CUSTOM_SCHEMA_FIELD = "custom_field_schema_version"
SUPPORTED_FIELD_TYPES = ("text", "number", "date", "select", "checkbox")
SUPPORTED_TARGETS = ("ELMS Course", "ELMS Program", "ELMS Batch")
MANAGER_ROLES = frozenset({"ELMS Company Admin", "ELMS Methodologist"})
PLATFORM_ROLES = frozenset({"Administrator", "System Manager", "ELMS Admin"})
FIELD_KEY_RE = re.compile(r"^[a-z][a-z0-9_]{1,63}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
PLATFORM_OWNER_NAME = "Демонстрационный контур НефтеГаз"


def _current_user() -> str:
    session = getattr(frappe, "session", None)
    return str(getattr(session, "user", "Guest") or "Guest")


def _roles(user: str | None = None) -> set[str]:
    current = user or _current_user()
    if current == "Administrator":
        return set(PLATFORM_ROLES)
    get_roles = getattr(frappe, "get_roles", None)
    return set(get_roles(current) or []) if callable(get_roles) else set()


def _throw(message: str, exception: type[Exception] | None = None) -> None:
    frappe.throw(message, exception or frappe.ValidationError)


def _text(value: Any, field: str, *, required: bool = True, limit: int = 140) -> str:
    result = str(value or "").strip()
    if required and not result:
        _throw(f"Поле {field} обязательно", frappe.ValidationError)
    if len(result) > limit:
        _throw(f"Поле {field} слишком длинное", frappe.ValidationError)
    return result


def _record_value(record: Any, field: str, default: Any = None) -> Any:
    if isinstance(record, Mapping):
        return record.get(field, default)
    getter = getattr(record, "get", None)
    if callable(getter):
        value = getter(field, default)
        if value is not None:
            return value
    return getattr(record, field, default)


def _set_record_value(record: Any, field: str, value: Any) -> None:
    if isinstance(record, dict):
        record[field] = value
        return
    setter = getattr(record, "set", None)
    if callable(setter):
        setter(field, value)
    else:
        setattr(record, field, value)


def _decode_json(value: Any, field: str) -> Any:
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (TypeError, ValueError, json.JSONDecodeError) as error:
            _throw(f"Поле {field} содержит некорректный JSON: {error}", frappe.ValidationError)
    return value


def _normalise_options(value: Any) -> list[str]:
    decoded = _decode_json(value, "options")
    if decoded is None or decoded == "":
        return []
    if isinstance(decoded, str):
        decoded = [line.strip() for line in decoded.splitlines() if line.strip()]
    if not isinstance(decoded, (list, tuple)):
        _throw("Опции должны быть списком строк", frappe.ValidationError)
    options = [_text(item, "options", limit=120) for item in decoded]
    if len(options) != len(set(options)):
        _throw("Опции не должны повторяться", frappe.ValidationError)
    return options


def _normalise_schema_version(value: Any) -> int:
    if isinstance(value, bool) or value in (None, ""):
        _throw("schema_version обязателен", frappe.ValidationError)
    try:
        version = int(value)
    except (TypeError, ValueError):
        _throw("schema_version должен быть целым числом", frappe.ValidationError)
    if version != SCHEMA_VERSION:
        _throw(f"Неподдерживаемая версия схемы: {version}", frappe.ValidationError)
    return version


def validate_definition_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and normalize one definition before it reaches Frappe."""
    if not isinstance(payload, Mapping):
        _throw("Определение поля должно быть объектом", frappe.ValidationError)
    organization = _text(payload.get("organization"), "organization")
    target = _text(payload.get("applies_to"), "applies_to")
    if target not in SUPPORTED_TARGETS:
        _throw("Этот тип документа не поддерживает дополнительные поля", frappe.ValidationError)
    field_key = _text(payload.get("field_key"), "field_key", limit=64).casefold()
    if not FIELD_KEY_RE.fullmatch(field_key):
        _throw("field_key должен начинаться с латинской буквы и содержать только a-z, 0-9 и _", frappe.ValidationError)
    label = _text(payload.get("label"), "label", limit=140)
    field_type = _text(payload.get("field_type"), "field_type").casefold()
    if field_type not in SUPPORTED_FIELD_TYPES:
        _throw(f"Недопустимый тип поля: {field_type}", frappe.ValidationError)
    options = _normalise_options(payload.get("options"))
    if field_type == "select" and not options:
        _throw("Для select нужен хотя бы один вариант", frappe.ValidationError)
    if field_type != "select" and options:
        _throw("Опции разрешены только для select", frappe.ValidationError)
    return {
        "organization": organization,
        "applies_to": target,
        "field_key": field_key,
        "label": label,
        "field_type": field_type,
        "options": options,
        "required": bool(payload.get("required", False)),
        "active": bool(payload.get("active", True)),
        "schema_version": _normalise_schema_version(payload.get("schema_version", SCHEMA_VERSION)),
        "description": str(payload.get("description") or "").strip(),
    }


def validate_definition_document(doc: Any) -> dict[str, Any]:
    """Apply the same scope and uniqueness checks to direct DocType writes."""
    payload = validate_definition_payload(doc.as_dict() if callable(getattr(doc, "as_dict", None)) else doc)
    require_custom_field_manager_access(payload["organization"])
    exists = getattr(getattr(frappe, "db", None), "exists", None)
    if callable(exists):
        filters: dict[str, Any] = {
            "organization": payload["organization"],
            "applies_to": payload["applies_to"],
            "field_key": payload["field_key"],
        }
        name = str(_record_value(doc, "name", "") or "")
        if name:
            filters["name"] = ["!=", name]
        if exists(DEFINITION_DOCTYPE, filters):
            _throw("Такой field_key уже существует для этого target", frappe.ValidationError)
    return payload


def _parse_values_payload(payload: Any) -> tuple[dict[str, Any], int | None]:
    decoded = _decode_json(payload, CUSTOM_VALUES_FIELD)
    if decoded is None:
        return {}, None
    if not isinstance(decoded, Mapping):
        _throw("custom_field_values должен быть JSON-объектом", frappe.ValidationError)
    values = decoded
    version = None
    if "values" in decoded:
        version = _normalise_schema_version(decoded.get("schema_version"))
        values = decoded.get("values")
        if not isinstance(values, Mapping):
            _throw("values должен быть JSON-объектом", frappe.ValidationError)
    return dict(values), version


def _is_empty(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _normalise_definition(record: Any) -> dict[str, Any]:
    return {
        "name": str(_record_value(record, "name", "") or ""),
        "organization": str(_record_value(record, "organization", "") or ""),
        "applies_to": str(_record_value(record, "applies_to", "") or ""),
        "field_key": str(_record_value(record, "field_key", "") or "").casefold(),
        "label": str(_record_value(record, "label", "") or ""),
        "field_type": str(_record_value(record, "field_type", "") or "").casefold(),
        "options": _normalise_options(_record_value(record, "options", [])),
        "required": bool(_record_value(record, "required", False)),
        "active": bool(_record_value(record, "active", True)),
        "schema_version": int(_record_value(record, "schema_version", SCHEMA_VERSION) or SCHEMA_VERSION),
    }


def validate_values(
    payload: Any,
    definitions: Iterable[Any],
    schema_version: Any = SCHEMA_VERSION,
) -> dict[str, Any]:
    """Validate typed values against definitions without performing persistence."""
    values, embedded_version = _parse_values_payload(payload)
    selected_version = embedded_version if embedded_version is not None else schema_version
    _normalise_schema_version(selected_version)
    definition_map = {
        definition["field_key"]: definition
        for definition in (_normalise_definition(item) for item in definitions)
        if definition["active"]
    }
    for definition in definition_map.values():
        _normalise_schema_version(definition["schema_version"])
    unknown_keys = sorted(set(values) - set(definition_map))
    if unknown_keys:
        _throw("Неизвестные ключи дополнительных полей: " + ", ".join(unknown_keys), frappe.ValidationError)
    for field_key, definition in definition_map.items():
        value = values.get(field_key)
        if definition["required"] and _is_empty(value):
            _throw(f"Поле {definition['label']} обязательно", frappe.ValidationError)
        if _is_empty(value):
            continue
        field_type = definition["field_type"]
        if field_type == "text" and not isinstance(value, str):
            _throw(f"Поле {definition['label']} должно быть текстом", frappe.ValidationError)
        elif field_type == "number":
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                _throw(f"Поле {definition['label']} должно быть числом", frappe.ValidationError)
        elif field_type == "date":
            if not isinstance(value, str) or not DATE_RE.fullmatch(value):
                _throw(f"Поле {definition['label']} должно быть датой YYYY-MM-DD", frappe.ValidationError)
            try:
                date.fromisoformat(value)
            except ValueError:
                _throw(f"Поле {definition['label']} содержит несуществующую дату", frappe.ValidationError)
        elif field_type == "select" and value not in definition["options"]:
            _throw(f"Поле {definition['label']} содержит неизвестную опцию", frappe.ValidationError)
        elif field_type == "checkbox" and not isinstance(value, bool):
            _throw(f"Поле {definition['label']} должно быть checkbox", frappe.ValidationError)
    return values


def _definitions_for(organization: str, target: str) -> list[dict[str, Any]]:
    get_all = getattr(frappe, "get_all", None)
    if not callable(get_all):
        return []
    rows = get_all(
        DEFINITION_DOCTYPE,
        filters={"organization": organization, "applies_to": target},
        fields=[
            "name",
            "organization",
            "applies_to",
            "field_key",
            "label",
            "field_type",
            "options",
            "required",
            "active",
            "schema_version",
        ],
        order_by="creation asc",
        limit_page_length=0,
    ) or []
    return [_normalise_definition(row) for row in rows]


def _is_platform_owner(organization: str) -> bool:
    if organization == PLATFORM_OWNER_NAME:
        return True
    db = getattr(frappe, "db", None)
    get_value = getattr(db, "get_value", None)
    if callable(get_value):
        try:
            return bool(get_value("ELMS Organization", organization, "is_platform_owner"))
        except (AttributeError, TypeError, RuntimeError):
            return False
    return False


def require_custom_field_manager_access(organization: str) -> str:
    """Authorize definition reads/writes for a manager in the selected scope."""
    organization_name = _text(organization, "organization")
    roles = _roles()
    if roles.intersection(PLATFORM_ROLES):
        if not _is_platform_owner(organization_name):
            _throw("Платформенный менеджер может работать только с каталогом owner-организации", frappe.PermissionError)
        return organization_name
    if roles.intersection(MANAGER_ROLES):
        if organization_membership_exists(_current_user(), organization_name):
            return organization_name
        _throw("Нет доступа к этой организации", frappe.PermissionError)
    _throw("Недостаточно прав для управления дополнительными полями", frappe.PermissionError)
    raise AssertionError("frappe.throw must raise")


def require_target_organization_access(organization: str) -> str:
    """Authorize target-document value reads/writes for the same org boundary."""
    organization_name = _text(organization, "organization")
    roles = _roles()
    if roles.intersection(PLATFORM_ROLES):
        return organization_name
    if roles.intersection(MANAGER_ROLES) and organization_membership_exists(_current_user(), organization_name):
        return organization_name
    if "ELMS Company Admin" in roles:
        return require_organization_access(organization_name)
    _throw("Нет доступа к данным этой организации", frappe.PermissionError)
    raise AssertionError("frappe.throw must raise")


def _target_name(value: Any) -> str:
    target = str(value or "").strip()
    if target not in SUPPORTED_TARGETS:
        _throw("Этот тип документа не поддерживает дополнительные поля", frappe.ValidationError)
    return target


def validate_document_values(doc: Any) -> dict[str, Any]:
    """Validate a target document and write its normalized JSON payload back."""
    target = _target_name(_record_value(doc, "doctype"))
    organization = require_target_organization_access(_record_value(doc, "organization"))
    raw_values = _record_value(doc, CUSTOM_VALUES_FIELD, {})
    version = _record_value(doc, CUSTOM_SCHEMA_FIELD, SCHEMA_VERSION) or SCHEMA_VERSION
    definitions = _definitions_for(organization, target)
    values = validate_values(raw_values, definitions, version)
    _set_record_value(doc, CUSTOM_VALUES_FIELD, values)
    _set_record_value(doc, CUSTOM_SCHEMA_FIELD, SCHEMA_VERSION)
    return values


def _stored_values(document: Any) -> dict[str, Any]:
    values, _ = _parse_values_payload(_record_value(document, CUSTOM_VALUES_FIELD, {}))
    return values


def resolve_effective_values(
    *,
    program: Any = None,
    course: Any = None,
    batch: Any = None,
) -> dict[str, Any]:
    """Merge Program defaults, Course overrides, and Batch overrides."""
    effective: dict[str, Any] = {}
    for document in (program, course, batch):
        if document is None:
            continue
        for field_key, value in _stored_values(document).items():
            if _is_empty(value):
                continue
            effective[field_key] = value
    return effective


def _load_document(target: str, name: str | None) -> Any:
    if not name or str(name).startswith("new-"):
        return {"doctype": target}
    get_doc = getattr(frappe, "get_doc", None)
    if not callable(get_doc):
        _throw("Не удалось загрузить документ", frappe.DoesNotExistError)
    return get_doc(target, name)


def effective_values_for_document(document: Any) -> dict[str, Any]:
    """Resolve the inheritance chain for one loaded target document."""
    target = _target_name(_record_value(document, "doctype"))
    if target == "ELMS Program":
        return resolve_effective_values(program=document)
    if target == "ELMS Course":
        program_name = str(_record_value(document, "program", "") or "")
        program = _load_document("ELMS Program", program_name) if program_name else None
        return resolve_effective_values(program=program, course=document)
    course_name = str(_record_value(document, "course", "") or "")
    course = _load_document("ELMS Course", course_name) if course_name else None
    program_name = str(_record_value(course, "program", "") or "") if course else ""
    program = _load_document("ELMS Program", program_name) if program_name else None
    return resolve_effective_values(program=program, course=course, batch=document)


def serialize_definition(definition: Any) -> dict[str, Any]:
    """Return a JSON-safe definition representation for whitelisted methods."""
    result = _normalise_definition(definition)
    result.pop("name", None)
    result["name"] = str(_record_value(definition, "name", "") or "")
    return result
