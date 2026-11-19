"""Whitelisted schema and target-form APIs for ELMS custom fields."""

from __future__ import annotations

import json
from typing import Any

import frappe

from elms.lms.custom_fields import (
    DEFINITION_DOCTYPE,
    SCHEMA_VERSION,
    SUPPORTED_TARGETS,
    _definitions_for,
    _load_document,
    _target_name,
    _text,
    effective_values_for_document,
    require_custom_field_manager_access,
    require_target_organization_access,
    serialize_definition,
    validate_definition_payload,
    validate_values,
)


if not hasattr(frappe, "ValidationError"):
    frappe.ValidationError = ValueError
if not hasattr(frappe, "PermissionError"):
    frappe.PermissionError = PermissionError
if not hasattr(frappe, "throw"):
    def _throw(message: str, exception: type[Exception] = Exception, *args: Any, **kwargs: Any) -> None:
        raise exception(message)

    frappe.throw = _throw


def _decode_payload(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, str):
        try:
            import json

            value = json.loads(value)
        except (TypeError, ValueError):
            frappe.throw("definition должен быть JSON-объектом", frappe.ValidationError)
    if not isinstance(value, dict):
        frappe.throw("definition должен быть JSON-объектом", frappe.ValidationError)
    return dict(value)


def _definition_from_args(
    definition: Any,
    organization: str | None,
    applies_to: str | None,
    field_key: str | None,
    label: str | None,
    field_type: str | None,
    options: Any,
    required: Any,
    active: Any,
    schema_version: Any,
    description: str | None,
) -> dict[str, Any]:
    payload = _decode_payload(definition)
    payload.update(
        {
            key: value
            for key, value in {
                "organization": organization,
                "applies_to": applies_to,
                "field_key": field_key,
                "label": label,
                "field_type": field_type,
                "options": options,
                "required": required,
                "active": active,
                "schema_version": schema_version,
                "description": description,
            }.items()
            if value is not None
        }
    )
    return payload


def _ensure_definition_scope(doc: Any, organization: str) -> None:
    existing_org = str(getattr(doc, "organization", "") or doc.get("organization", ""))
    if existing_org != organization:
        frappe.throw("Нет доступа к схеме другой организации", frappe.PermissionError)


def _save_document(doc: Any) -> Any:
    flags = getattr(doc, "flags", None)
    if flags is not None:
        flags.ignore_permissions = True
    save = getattr(doc, "save", None)
    if callable(save):
        return save(ignore_permissions=True)
    insert = getattr(doc, "insert", None)
    if callable(insert):
        return insert(ignore_permissions=True)
    frappe.throw("Не удалось сохранить определение поля", frappe.ValidationError)


def _document_payload(validated: dict[str, Any]) -> dict[str, Any]:
    payload = dict(validated)
    payload["options"] = json.dumps(validated["options"], ensure_ascii=False)
    return payload


def _document_for_effective_values(document: Any, target: str, organization: str) -> Any:
    if target != "ELMS Course":
        return document
    program = str(getattr(document, "program", "") or document.get("program", "")).strip()
    if not program:
        return document
    get_value = getattr(getattr(frappe, "db", None), "get_value", None)
    if not callable(get_value):
        return document
    program_name = get_value(
        "ELMS Program",
        {"name": program, "organization": organization},
        "name",
    ) or get_value(
        "ELMS Program",
        {"program_name": program, "organization": organization},
        "name",
    )
    if not program_name:
        return document
    as_dict = getattr(document, "as_dict", None)
    if not callable(as_dict):
        return document
    projected = as_dict()
    projected["program"] = str(program_name)
    return projected


@frappe.whitelist()
def get_custom_field_schema(
    target_doctype: str,
    organization: str,
) -> dict[str, Any]:
    """Return the active and inactive definitions visible in one organization."""
    target = _target_name(target_doctype)
    organization_name = require_custom_field_manager_access(organization)
    definitions = _definitions_for(organization_name, target)
    return {
        "organization": organization_name,
        "target_doctype": target,
        "schema_version": SCHEMA_VERSION,
        "definitions": [serialize_definition(item) for item in definitions],
    }


@frappe.whitelist()
def save_custom_field_definition(
    definition: Any = None,
    organization: str | None = None,
    applies_to: str | None = None,
    field_key: str | None = None,
    label: str | None = None,
    field_type: str | None = None,
    options: Any = None,
    required: Any = None,
    active: Any = None,
    schema_version: Any = None,
    description: str | None = None,
) -> dict[str, Any]:
    """Create or update one definition after scope and schema validation."""
    payload = _definition_from_args(
        definition,
        organization,
        applies_to,
        field_key,
        label,
        field_type,
        options,
        required,
        active,
        schema_version,
        description,
    )
    organization_name = require_custom_field_manager_access(payload.get("organization"))
    payload["organization"] = organization_name
    name = str(payload.pop("name", "") or "")
    validated = validate_definition_payload(payload)
    document_payload = _document_payload(validated)

    if name:
        doc = frappe.get_doc(DEFINITION_DOCTYPE, name)
        _ensure_definition_scope(doc, organization_name)
        if str(getattr(doc, "applies_to", "") or doc.get("applies_to", "")) != validated["applies_to"]:
            frappe.throw("Нельзя менять target существующего поля", frappe.ValidationError)
        doc.update(document_payload)
        _save_document(doc)
    else:
        exists = getattr(getattr(frappe, "db", None), "exists", None)
        if callable(exists) and exists(
            DEFINITION_DOCTYPE,
            {
                "organization": organization_name,
                "applies_to": validated["applies_to"],
                "field_key": validated["field_key"],
            },
        ):
            frappe.throw("Такой field_key уже существует для этого target", frappe.ValidationError)
        doc = frappe.get_doc({"doctype": DEFINITION_DOCTYPE, **document_payload})
        _save_document(doc)
    return {"definition": serialize_definition(doc), "schema_version": SCHEMA_VERSION}


@frappe.whitelist()
def delete_custom_field_definition(name: str, organization: str) -> dict[str, Any]:
    """Delete one definition only inside the manager's organization scope."""
    organization_name = require_custom_field_manager_access(organization)
    definition_name = _text(name, "name")
    doc = frappe.get_doc(DEFINITION_DOCTYPE, definition_name)
    _ensure_definition_scope(doc, organization_name)
    delete = getattr(doc, "delete", None)
    if not callable(delete):
        frappe.throw("Не удалось удалить определение поля", frappe.ValidationError)
    delete(ignore_permissions=True)
    return {"name": definition_name, "organization": organization_name, "status": "deleted"}


@frappe.whitelist()
def get_custom_field_form_data(
    target_doctype: str,
    target_name: str | None = None,
    organization: str | None = None,
) -> dict[str, Any]:
    """Return schema, stored values, and effective inherited values for a form."""
    target = _target_name(target_doctype)
    requested_org = str(organization or "").strip()
    if target_name and not str(target_name).startswith("new-"):
        document = _load_document(target, target_name)
        document_org = str(getattr(document, "organization", "") or document.get("organization", ""))
        organization_name = require_target_organization_access(requested_org or document_org)
        if document_org != organization_name:
            frappe.throw("Нет доступа к документу другой организации", frappe.PermissionError)
    else:
        organization_name = require_target_organization_access(requested_org)
        document = {"doctype": target, "organization": organization_name}

    definitions = _definitions_for(organization_name, target)
    stored_values = getattr(document, "custom_field_values", None)
    if stored_values is None and hasattr(document, "get"):
        stored_values = document.get("custom_field_values")
    stored_values = validate_values(
        stored_values or {},
        definitions,
        getattr(document, "custom_field_schema_version", SCHEMA_VERSION) or SCHEMA_VERSION,
    )
    effective_document = _document_for_effective_values(document, target, organization_name)
    return {
        "organization": organization_name,
        "target_doctype": target,
        "target_name": str(target_name or ""),
        "schema_version": SCHEMA_VERSION,
        "definitions": [serialize_definition(item) for item in definitions],
        "stored_values": stored_values,
        "effective_values": effective_values_for_document(effective_document),
    }
