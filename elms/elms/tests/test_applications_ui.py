"""Contracts for public tracking and the operator application surface."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]


class TestApplicationsUI(unittest.TestCase):
    def setUp(self):
        app_root = ROOT / "elms"
        self.js = (app_root / "public" / "js" / "desk-applications.js").read_text(encoding="utf-8")
        self.css = (app_root / "public" / "css" / "desk-applications.css").read_text(encoding="utf-8")
        self.status_html = (app_root / "www" / "apply" / "status.html").read_text(encoding="utf-8")
        self.hooks = (app_root / "hooks.py").read_text(encoding="utf-8")

    def test_desk_assets_and_role_gated_page_are_registered(self):
        self.assertIn("desk-applications.css", self.hooks)
        self.assertIn("desk-applications.js", self.hooks)
        self.assertIn('frappe.standard_pages[pageName]', self.js)

    def test_desk_uses_real_list_and_refresh_methods(self):
        self.assertIn("elms.applications.api.list_application_links", self.js)
        self.assertIn("elms.applications.api.refresh_application_status", self.js)
        self.assertIn("Статус из Bitrix", self.js)
        self.assertIn("aria-live=\"polite\"", self.js)

    def test_public_tracking_uses_snapshot_and_refresh_control(self):
        self.assertIn("Обновить сохранённые данные", self.status_html)
        self.assertIn('data-status-badge', self.status_html)
        self.assertIn("Статус из Bitrix", self.status_html)

    def test_status_map_is_configured_and_desk_markup_is_safe(self):
        settings = json.loads((ROOT / "elms_core" / "doctype" / "elms_application_settings" / "elms_application_settings.json").read_text(encoding="utf-8"))
        fields = {field["fieldname"]: field for field in settings["fields"]}
        self.assertIn("status_map", fields)
        self.assertIn("CONVERTED", fields["status_map"]["default"])
        self.assertIn(":focus-visible", self.css)
        self.assertNotIn("crm.deal", self.js)

    def test_application_shortcut_is_operator_only(self):
        from elms.desk.workspaces import filter_workspace_for_user

        page = {
            "shortcuts": [
                {"url": "/app/elms-course-studio", "shortcut_name": "Конструктор курсов"},
                {"url": "/app/elms-applications", "shortcut_name": "Заявки из Bitrix"},
            ],
            "content": json.dumps([
                {"type": "shortcut", "data": {"shortcut_name": "Конструктор курсов"}},
                {"type": "shortcut", "data": {"shortcut_name": "Заявки из Bitrix"}},
            ], ensure_ascii=False),
        }
        with patch("elms.desk.workspaces.frappe.get_roles", return_value=["ELMS Methodologist"], create=True):
            filtered = filter_workspace_for_user(page, "LMS", "methodologist@example.test")
        self.assertNotIn("/app/elms-applications", {item["url"] for item in filtered["shortcuts"]})


if __name__ == "__main__":
    unittest.main()
