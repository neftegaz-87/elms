from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class TestAdmissionImportUI(unittest.TestCase):
    def setUp(self):
        self.js = (ROOT / "elms" / "public" / "js" / "desk-admission.js").read_text(encoding="utf-8")
        self.css = (ROOT / "elms" / "public" / "css" / "desk-admission.css").read_text(encoding="utf-8")
        self.page = json.loads((ROOT / "elms" / "operations" / "page" / "elms_admission" / "elms_admission.json").read_text(encoding="utf-8"))

    def test_company_admin_page_exposes_upload_preview_export_and_reveal_paths(self):
        for token in (
            "ELMS Company Admin",
            "data-admission-import",
            "upload_import",
            "inspect_import",
            "export_import",
            "reveal_credential",
            "invite-token",
            "admission-xlsx-v1",
        ):
            self.assertIn(token, self.js)

    def test_preview_has_explicit_error_and_keyboard_states(self):
        self.assertIn("data-admission-import-status aria-live=\"polite\"", self.js)
        self.assertIn("data-admission-import-rows", self.js)
        self.assertIn(":focus-visible", self.css)
        self.assertIn("prefers-reduced-motion", self.css)
        self.assertIn({"role": "ELMS Company Admin"}, self.page["roles"])

    def test_reveal_is_explicit_and_no_secret_is_in_initial_preview(self):
        self.assertIn("reveal_intent: true", self.js)
        self.assertIn("result.invite_token", self.js)
        self.assertNotIn("invite_token: row", self.js)


if __name__ == "__main__":
    unittest.main()
