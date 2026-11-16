"""Desk cabinet route and server-call contracts."""

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class TestCabinetUI(unittest.TestCase):
    def setUp(self):
        self.js = (ROOT / "elms" / "public" / "js" / "desk-cabinet.js").read_text(encoding="utf-8")
        self.page_js = (ROOT / "elms" / "public" / "js" / "elms-cabinet-page.js").read_text(encoding="utf-8")
        self.page_json = (ROOT / "elms" / "operations" / "page" / "elms_cabinet" / "elms_cabinet.json").read_text(encoding="utf-8")
        self.css = (ROOT / "elms" / "public" / "css" / "desk-cabinet.css").read_text(encoding="utf-8")
        self.hooks = (ROOT / "elms" / "hooks.py").read_text(encoding="utf-8")
        self.api = (ROOT / "elms" / "cabinet" / "api.py").read_text(encoding="utf-8")

    def test_cabinet_assets_and_route_are_registered(self):
        self.assertIn("desk-cabinet.css", self.hooks)
        self.assertIn("desk-cabinet.js", self.hooks)
        self.assertIn('"elms-cabinet": "public/js/elms-cabinet-page.js"', self.hooks)
        self.assertIn('frappe.pages["elms-cabinet"].on_page_load', self.page_js)
        self.assertIn('frappe.require("/assets/elms/js/desk-cabinet.js", start)', self.page_js)
        self.assertNotIn("desk-cabinet.js?", self.page_js)
        self.assertIn("elms-cabinet-css-inline", self.js)
        self.assertIn("window.elmsCabinetPage", self.js)
        self.assertNotIn("frappe.standard_pages", self.js)
        self.assertIn('"name": "elms-cabinet"', self.page_json)
        self.assertIn('"role": "ELMS Company Admin"', self.page_json)

    def test_cabinet_calls_real_server_roster_and_renders_empty_state(self):
        self.assertIn("elms.cabinet.api.get_org_roster", self.js)
        self.assertIn("get_org_roster", self.js)
        self.assertIn("data-cabinet-empty", self.js)
        self.assertIn("Пока нет сотрудников", self.js)
        self.assertIn("aria-live=\"polite\"", self.js)
        self.assertIn(":focus-visible", self.css)
        self.assertIn("@media", self.css)

    def test_cabinet_does_not_use_client_side_user_list_as_security(self):
        self.assertIn("require_organization_access", (ROOT / "elms" / "cabinet" / "roster.py").read_text(encoding="utf-8"))
        self.assertIn("build_org_roster", self.api)
        self.assertNotIn("get_all(\"User\")", self.js)
        self.assertNotIn("downloadCSV", self.js)


if __name__ == "__main__":
    unittest.main()
