"""Contracts for the B2B organization and invite Desk surface."""

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class TestAccessUI(unittest.TestCase):
    def setUp(self):
        self.js = (ROOT / "elms" / "public" / "js" / "desk-access.js").read_text(encoding="utf-8")
        self.page_js = (ROOT / "elms" / "public" / "js" / "elms-access-page.js").read_text(encoding="utf-8")
        self.page_json = (ROOT / "elms" / "operations" / "page" / "elms_access" / "elms_access.json").read_text(encoding="utf-8")
        self.css = (ROOT / "elms" / "public" / "css" / "desk-access.css").read_text(encoding="utf-8")
        self.hooks = (ROOT / "elms" / "hooks.py").read_text(encoding="utf-8")

    def test_company_role_access_surface_is_registered_separately_from_settings(self):
        page_js = (ROOT / "elms" / "public" / "js" / "elms-company-access-page.js").read_text(encoding="utf-8")
        page_json = (ROOT / "elms" / "operations" / "page" / "elms_company_access" / "elms_company_access.json").read_text(encoding="utf-8")
        js = (ROOT / "elms" / "public" / "js" / "desk-company-access.js").read_text(encoding="utf-8")
        self.assertIn('"elms-company-access": "public/js/elms-company-access-page.js"', self.hooks)
        self.assertIn('frappe.pages["elms-company-access"].on_page_load', page_js)
        self.assertIn('"role": "ELMS Company Admin"', page_json)
        self.assertIn('elms.access.api.get_company_access_context', js)
        self.assertIn('elms.access.api.update_organization_member', js)
        self.assertIn('elms.access.api.disable_organization_member', js)
        self.assertIn('elms.access.api.invite_org_user', js)
        self.assertIn('create_organization_role', js)
        self.assertIn('update_organization_role', js)
        self.assertIn('delete_organization_role', js)
        self.assertIn('organization_role', js)
        self.assertIn("Глобальные настройки", js)
        self.assertIn('role="tablist"', js)
        self.assertIn('data-company-access-tab="invite"', js)
        self.assertIn('data-company-access-tab="members"', js)
        self.assertIn('data-company-access-tab="roles"', js)
        self.assertIn('role="tabpanel"', js)
        self.assertIn('ArrowRight', js)
        self.assertIn('page-change.elmsCompanyAccess', js)
        self.assertIn('ensureCompanyAccessStyles', js)
        self.assertIn('on_page_show', page_js)

    def test_access_assets_are_registered_and_route_is_available(self):
        self.assertIn("desk-access.css", self.hooks)
        self.assertIn("desk-access.js", self.hooks)
        self.assertIn('"elms-access": "public/js/elms-access-page.js"', self.hooks)
        self.assertIn('accessPageName = "elms-access"', self.js)
        self.assertIn("frappe.standard_pages[accessPageName]", self.js)
        self.assertIn('frappe.pages["elms-access"].on_page_load', self.page_js)
        self.assertIn('"name": "elms-access"', self.page_json)
        self.assertIn('"module": "Operations"', self.page_json)
        self.assertNotIn('"role": "ELMS Company Admin"', self.page_json)

    def test_access_surface_calls_real_server_methods(self):
        for method in (
            "elms.access.api.create_organization",
            "elms.access.api.assign_company_admin",
            "elms.access.api.invite_org_user",
            "elms.access.api.get_company_access_context",
        ):
            self.assertIn(method, self.js)
        self.assertIn("frappe.call", self.js)
        self.assertIn("Company Admin", self.js)
        self.assertIn("aria-live=\"polite\"", self.js)

    def test_access_surface_splits_actions_into_tabs_with_org_select(self):
        self.assertIn('role="tablist"', self.js)
        self.assertIn('data-access-tab="organization"', self.js)
        self.assertIn('data-access-tab="company-admin"', self.js)
        self.assertIn('data-access-tab="invite"', self.js)
        self.assertIn('role="tabpanel"', self.js)
        self.assertIn('data-access-panel="organization"', self.js)
        self.assertIn('data-access-panel="company-admin"', self.js)
        self.assertIn('data-access-panel="invite"', self.js)
        self.assertIn("ArrowRight", self.js)
        self.assertIn('data-access-org-select="invite"', self.js)
        self.assertIn('data-access-org-select="company-admin"', self.js)
        self.assertIn("loadOrganizations", self.js)
        self.assertIn(".elms-access-tabs", self.css)
        self.assertIn(".elms-access-tab.is-active", self.css)
        self.assertIn(".elms-access-panel", self.css)

    def test_access_surface_has_role_and_error_states_without_client_security(self):
        self.assertIn("ELMS Admin", self.js)
        self.assertIn("ELMS Company Admin", self.js)
        self.assertIn("Проверьте права", self.js)
        self.assertIn(".elms-access-status.error", self.css)
        self.assertNotIn("filter.*organization", self.js)
        self.assertNotIn("kc_idp_hint=yandex", self.js)

    def test_access_css_has_keyboard_focus_and_responsive_layout(self):
        self.assertIn(".elms-access-shell", self.css)
        self.assertIn(":focus-visible", self.css)
        self.assertIn("@media", self.css)

    def test_company_access_css_has_separate_tab_surface(self):
        css = (ROOT / "elms" / "public" / "css" / "desk-company-access.css").read_text(encoding="utf-8")
        self.assertIn(".elms-company-access-tabs", css)
        self.assertIn(".elms-company-access-tab.is-active", css)
        self.assertIn(".elms-company-access-panel", css)

    def test_access_workspace_links_to_real_doctypes_and_route(self):
        from elms.desk.workspaces import ELMS_WORKSPACE_DEFINITIONS

        access = next(item for item in ELMS_WORKSPACE_DEFINITIONS if item["name"] == "B2B Access")
        self.assertEqual(access["roles"], ("ELMS Admin", "ELMS Operations User"))
        self.assertEqual(access["shortcuts"][0]["url"], "/app/elms-access")
        links = {link_to for _, link_to, _ in access["links"]}
        self.assertEqual(
            links,
            {"ELMS Organization", "ELMS Organization Member", "ELMS Invite Log"},
        )

    def test_access_page_contract_is_json_safe(self):
        from elms.desk.workspaces import _workspace_content, ELMS_WORKSPACE_DEFINITIONS

        access = next(item for item in ELMS_WORKSPACE_DEFINITIONS if item["name"] == "B2B Access")
        blocks = json.loads(_workspace_content(access["content"], access["links"], access["shortcuts"]))
        self.assertTrue(any(block.get("type") == "shortcut" for block in blocks))


if __name__ == "__main__":
    unittest.main()
