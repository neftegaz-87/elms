"""Behavior contracts for the org-scoped ELMS custom-field boundary."""

import unittest
from types import SimpleNamespace
from unittest.mock import patch

import frappe

from elms.lms import custom_fields


DEFINITIONS = [
    {
        "field_key": "delivery_mode",
        "label": "Delivery mode",
        "field_type": "select",
        "options": ["Online", "In person"],
        "required": True,
        "active": True,
        "schema_version": 1,
    },
    {
        "field_key": "academic_hours_override",
        "label": "Academic hours",
        "field_type": "number",
        "options": [],
        "required": False,
        "active": True,
        "schema_version": 1,
    },
    {
        "field_key": "starts_on",
        "label": "Starts on",
        "field_type": "date",
        "options": [],
        "required": False,
        "active": True,
        "schema_version": 1,
    },
    {
        "field_key": "is_recorded",
        "label": "Is recorded",
        "field_type": "checkbox",
        "options": [],
        "required": False,
        "active": True,
        "schema_version": 1,
    },
]


class TestCustomFieldDefinitions(unittest.TestCase):
    def test_definition_accepts_only_the_mvp_types_and_targets(self):
        self.assertEqual(
            custom_fields.SUPPORTED_FIELD_TYPES,
            ("text", "number", "date", "select", "checkbox"),
        )
        self.assertEqual(
            custom_fields.SUPPORTED_TARGETS,
            ("ELMS Course", "ELMS Program", "ELMS Batch"),
        )

        for field_type in custom_fields.SUPPORTED_FIELD_TYPES:
            payload = {
                "organization": "ORG-1",
                "applies_to": "ELMS Course",
                "field_key": f"field_{field_type}",
                "label": "A field",
                "field_type": field_type,
                "options": ["A", "B"] if field_type == "select" else [],
                "schema_version": 1,
            }
            result = custom_fields.validate_definition_payload(payload)
            self.assertEqual(result["field_type"], field_type)

    def test_select_definitions_require_options_and_unknown_targets_fail_closed(self):
        select_payload = {
            "organization": "ORG-1",
            "applies_to": "ELMS Course",
            "field_key": "delivery_mode",
            "label": "Delivery mode",
            "field_type": "select",
            "options": [],
            "schema_version": 1,
        }
        with self.assertRaises(frappe.ValidationError):
            custom_fields.validate_definition_payload(select_payload)

        unsupported = dict(select_payload, applies_to="ELMS Course Lesson", options=["A"])
        with self.assertRaises(frappe.ValidationError):
            custom_fields.validate_definition_payload(unsupported)

    def test_definition_key_is_stable_and_normalized(self):
        result = custom_fields.validate_definition_payload(
            {
                "organization": "ORG-1",
                "applies_to": "ELMS Course",
                "field_key": "  Delivery_Mode ",
                "label": " Delivery mode ",
                "field_type": "text",
                "schema_version": 1,
            }
        )
        self.assertEqual(result["field_key"], "delivery_mode")
        self.assertEqual(result["label"], "Delivery mode")


class TestCustomFieldValues(unittest.TestCase):
    def test_valid_values_include_zero_and_false(self):
        result = custom_fields.validate_values(
            {
                "delivery_mode": "Online",
                "academic_hours_override": 0,
                "starts_on": "2026-11-19",
                "is_recorded": False,
            },
            DEFINITIONS,
        )
        self.assertEqual(result["academic_hours_override"], 0)
        self.assertIs(result["is_recorded"], False)

    def test_invalid_values_are_rejected_before_persistence(self):
        invalid_values = (
            {"delivery_mode": "Unknown"},
            {"delivery_mode": "Online", "academic_hours_override": True},
            {"delivery_mode": "Online", "starts_on": "19.11.2026"},
            {"delivery_mode": "Online", "is_recorded": "false"},
            {"academic_hours_override": 1},
            {"delivery_mode": "Online", "unexpected": "value"},
        )
        for values in invalid_values:
            with self.subTest(values=values):
                with self.assertRaises(frappe.ValidationError):
                    custom_fields.validate_values(values, DEFINITIONS)

    def test_incompatible_schema_versions_fail_closed(self):
        with self.assertRaises(frappe.ValidationError):
            custom_fields.validate_values(
                {"schema_version": 2, "values": {"delivery_mode": "Online"}},
                DEFINITIONS,
            )

    def test_program_course_batch_inheritance_keeps_explicit_zero_and_false(self):
        program = {"custom_field_values": {"delivery_mode": "Online", "academic_hours_override": 12, "is_recorded": True}}
        course = {"custom_field_values": {"delivery_mode": "", "academic_hours_override": 0}}
        batch = {"custom_field_values": {"is_recorded": False}}

        result = custom_fields.resolve_effective_values(
            program=program,
            course=course,
            batch=batch,
        )

        self.assertEqual(result["delivery_mode"], "Online")
        self.assertEqual(result["academic_hours_override"], 0)
        self.assertIs(result["is_recorded"], False)

    def test_document_values_are_versioned_and_use_the_common_validator(self):
        doc = SimpleNamespace(
            doctype="ELMS Course",
            organization="ORG-1",
            custom_field_schema_version=1,
            custom_field_values={"delivery_mode": "Online"},
        )
        with (
            patch.object(custom_fields, "_definitions_for", return_value=DEFINITIONS),
            patch.object(custom_fields, "require_target_organization_access", return_value="ORG-1"),
        ):
            result = custom_fields.validate_document_values(doc)
        self.assertEqual(result, {"delivery_mode": "Online"})


class TestCustomFieldOrganizationScope(unittest.TestCase):
    def test_company_admin_can_manage_only_a_member_organization(self):
        with (
            patch.object(frappe, "get_roles", return_value=["ELMS Company Admin"], create=True),
            patch.object(custom_fields, "organization_membership_exists", return_value=True),
            patch.object(custom_fields, "_current_user", return_value="admin@example.test"),
        ):
            self.assertEqual(
                custom_fields.require_custom_field_manager_access("ORG-1"),
                "ORG-1",
            )

    def test_foreign_organization_is_denied_for_company_admin(self):
        with (
            patch.object(frappe, "get_roles", return_value=["ELMS Company Admin"], create=True),
            patch.object(custom_fields, "organization_membership_exists", return_value=False),
            patch.object(custom_fields, "_current_user", return_value="admin@example.test"),
        ):
            with self.assertRaises(frappe.PermissionError):
                custom_fields.require_custom_field_manager_access("FOREIGN-ORG")

    def test_platform_manager_is_limited_to_owner_organization(self):
        with (
            patch.object(frappe, "get_roles", return_value=["ELMS Admin"], create=True),
            patch.object(custom_fields, "_current_user", return_value="platform@example.test"),
            patch.object(custom_fields, "_is_platform_owner", side_effect=lambda value: value == "OWNER"),
        ):
            self.assertEqual(
                custom_fields.require_custom_field_manager_access("OWNER"),
                "OWNER",
            )
            with self.assertRaises(frappe.PermissionError):
                custom_fields.require_custom_field_manager_access("PARTNER")


if __name__ == "__main__":
    unittest.main()
