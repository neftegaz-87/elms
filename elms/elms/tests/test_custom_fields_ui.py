"""Wire and Desk-surface contracts for custom fields."""

import json
import unittest
from pathlib import Path

from elms.desk.workspaces import ELMS_WORKSPACE_DEFINITIONS


ROOT = Path(__file__).resolve().parents[1]


class TestCustomFieldsDeskSurface(unittest.TestCase):
    def test_target_doctypes_have_the_versioned_json_payload(self):
        for path in (
            "lms/doctype/elms_course/elms_course.json",
            "lms/doctype/elms_program/elms_program.json",
            "lms/doctype/elms_batch/elms_batch.json",
        ):
            manifest = json.loads((ROOT / path).read_text())
            fieldnames = {field["fieldname"] for field in manifest["fields"]}
            labels = {field.get("label") for field in manifest["fields"]}
            self.assertIn("custom_field_values", fieldnames)
            self.assertIn("custom_field_schema_version", fieldnames)
            self.assertIn("Additional fields", labels)

    def test_definition_doctype_manifest_is_org_scoped_and_role_gated(self):
        manifest = json.loads(
            (ROOT / "lms/doctype/elms_custom_field_definition/elms_custom_field_definition.json").read_text()
        )
        fieldnames = {field["fieldname"] for field in manifest["fields"]}
        self.assertTrue({"organization", "applies_to", "field_key", "field_type", "schema_version"} <= fieldnames)
        roles = {permission["role"] for permission in manifest["permissions"]}
        self.assertTrue({"ELMS Company Admin", "ELMS Methodologist", "ELMS Admin", "System Manager"} <= roles)

    def test_workspace_exposes_the_schema_manager_route(self):
        lms = next(item for item in ELMS_WORKSPACE_DEFINITIONS if item["name"] == "LMS")
        shortcuts = {shortcut["url"] for shortcut in lms["shortcuts"]}
        self.assertIn("/app/elms-custom-fields", shortcuts)

    def test_hooks_wire_the_same_form_script_and_manager_page(self):
        hooks = (ROOT / "hooks.py").read_text()
        self.assertIn('"ELMS Course": "public/js/custom-fields.js"', hooks)
        self.assertIn('"ELMS Program": "public/js/custom-fields.js"', hooks)
        self.assertIn('"ELMS Batch": "public/js/custom-fields.js"', hooks)
        self.assertIn('"elms-custom-fields": "public/js/elms-custom-fields-page.js"', hooks)
        self.assertIn("/assets/elms/css/custom-fields.css", hooks)

    def test_ui_calls_the_canonical_server_boundary(self):
        form_js = (ROOT / "public/js/custom-fields.js").read_text()
        page_js = (ROOT / "public/js/elms-custom-fields-page.js").read_text()
        api_py = (ROOT / "lms/api/custom_fields.py").read_text()
        self.assertIn("get_custom_field_form_data", form_js)
        self.assertIn("get_custom_field_schema", page_js)
        self.assertIn("save_custom_field_definition", page_js)
        self.assertIn("get_custom_field_schema", api_py)
        self.assertIn("save_custom_field_definition", api_py)
        self.assertIn("get_custom_field_form_data", api_py)

    def test_custom_field_surface_has_no_unsupported_learning_graph_entry(self):
        paths = (
            ROOT / "lms/api/custom_fields.py",
            ROOT / "lms/custom_fields.py",
            ROOT / "public/js/custom-fields.js",
            ROOT / "public/js/elms-custom-fields-page.js",
            ROOT / "lms/page/elms_custom_fields/elms_custom_fields.json",
        )
        combined = "\n".join(path.read_text() for path in paths)
        self.assertNotRegex(combined, r"Chapter|Lesson|Category")


if __name__ == "__main__":
    unittest.main()
