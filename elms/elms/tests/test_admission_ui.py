"""Desk admission page and production call-site contracts."""

from __future__ import annotations

import unittest
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class TestAdmissionUI(unittest.TestCase):
    def setUp(self):
        self.js = (ROOT / "elms" / "public" / "js" / "desk-admission.js").read_text(encoding="utf-8")
        self.page_js = (ROOT / "elms" / "public" / "js" / "elms-admission-page.js").read_text(encoding="utf-8")
        self.page_json = (ROOT / "elms" / "operations" / "page" / "elms_admission" / "elms_admission.json").read_text(encoding="utf-8")
        self.css = (ROOT / "elms" / "public" / "css" / "desk-admission.css").read_text(encoding="utf-8")
        self.hooks = (ROOT / "elms" / "hooks.py").read_text(encoding="utf-8")
        self.workspace = (ROOT / "elms" / "desk" / "workspaces.py").read_text(encoding="utf-8")
        self.install = (ROOT / "elms" / "install.py").read_text(encoding="utf-8")

    def test_admission_route_and_assets_are_registered(self):
        self.assertIn('"elms-admission": "public/js/elms-admission-page.js"', self.hooks)
        self.assertIn("desk-admission.css", self.hooks)
        self.assertIn("desk-admission.js", self.hooks)
        self.assertIn('frappe.pages["elms-admission"].on_page_load', self.page_js)
        self.assertIn('frappe.require("/assets/elms/js/desk-admission.js", start)', self.page_js)
        self.assertIn('"name": "elms-admission"', self.page_json)
        self.assertIn('"role": "ELMS Learner"', self.page_json)

    def test_form_uses_real_profile_api_and_required_private_scan_contract(self):
        for token in (
            "elms.admission.api.get_profile",
            "elms.admission.api.save_profile",
            "passport_scan",
            "snils_scan",
            "education_doc_scan",
            "consent_version",
            "LearnerProfile",
        ):
            self.assertIn(token, self.js)
        self.assertIn("data-admission-course", self.js)
        self.assertIn("data-admission-batch", self.js)
        self.assertIn("data-admission-status", self.js)
        self.assertIn("frappe.get_route", self.js)
        self.assertIn('selected"', self.js)

    def test_admission_page_has_empty_error_and_keyboard_states(self):
        self.assertIn("Профиль ещё не заполнен", self.js)
        self.assertIn("aria-live=\"polite\"", self.js)
        self.assertIn(":focus-visible", self.css)
        self.assertIn("@media", self.css)
        self.assertIn("/app/elms-admission", self.workspace)

    def test_no_public_file_url_is_rendered_as_profile_data(self):
        self.assertNotIn("file_url", self.js)
        self.assertNotIn("/files/", self.js)
        self.assertIn("ELMS Payment", self.js)
        self.assertIn("ручная отметка недоступна", self.js)

    def test_consent_checkbox_cannot_submit_unchecked_version(self):
        self.assertIn('consent.checked ? consent.value : ""', self.js)

    def test_admission_doctype_defines_unique_profile_and_private_acl(self):
        path = ROOT / "elms" / "elms_core" / "doctype" / "elms_admission_profile" / "elms_admission_profile.json"
        doctype = json.loads(path.read_text(encoding="utf-8"))
        fields = {field["fieldname"]: field for field in doctype["fields"]}
        self.assertEqual(doctype["name"], "ELMS Admission Profile")
        self.assertEqual(doctype["module"], "ELMS Core")
        self.assertEqual(fields["user"]["unique"], 1)
        for fieldname in ("passport_scan", "snils_scan", "education_doc_scan"):
            self.assertEqual(fields[fieldname]["fieldtype"], "Attach")
            self.assertEqual(fields[fieldname]["read_only"], 1)
        self.assertEqual(fields["consent_version"]["reqd"], 1)
        self.assertEqual(fields["consent_timestamp"]["read_only"], 1)
        permissions = {permission["role"]: permission for permission in doctype["permissions"]}
        self.assertEqual(permissions["ELMS Learner"]["read"], 1)
        self.assertEqual(permissions["ELMS Learner"]["write"], 1)
        self.assertEqual(permissions["ELMS Operations User"]["read"], 1)
        self.assertEqual(permissions["ELMS Operations User"]["write"], 0)
        self.assertEqual(permissions["ELMS Admin"]["delete"], 0)

    def test_admission_profile_install_permissions_are_registered(self):
        self.assertIn("def ensure_admission_profile_permissions", self.install)
        self.assertIn("ensure_admission_profile_permissions()", self.install)


if __name__ == "__main__":
    unittest.main()
