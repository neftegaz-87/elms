"""Tests for ELMS Learning Desk page, player surface, and anti-cheat telemetry."""

import unittest
from pathlib import Path


class TestLearningUI(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parents[2]
        self.js_path = self.root / "elms" / "public" / "js" / "desk-learning.js"
        self.css_path = self.root / "elms" / "public" / "css" / "desk-learning.css"
        self.hooks_path = self.root / "elms" / "hooks.py"
        self.workspaces_path = self.root / "elms" / "desk" / "workspaces.py"

    def test_learning_assets_exist(self):
        """desk-learning.js and desk-learning.css must exist."""
        self.assertTrue(self.js_path.is_file(), "desk-learning.js must exist")
        self.assertTrue(self.css_path.is_file(), "desk-learning.css must exist")

    def test_learning_assets_registered_in_hooks(self):
        """Assets must be included in app_include_css and app_include_js."""
        content = self.hooks_path.read_text(encoding="utf-8")
        self.assertIn("desk-learning.css", content)
        self.assertIn("desk-learning.js", content)

    def test_learning_css_tokens_and_classes(self):
        """CSS must follow Neftegaz light tokens and define player classes."""
        css = self.css_path.read_text(encoding="utf-8")
        self.assertIn("--elms-action: #0d4cd3;", css)
        self.assertIn("--elms-paper: #f5f7fa;", css)
        self.assertIn(".elms-learning-shell", css)
        self.assertIn(".elms-course-card", css)
        self.assertIn(".elms-player-container", css)
        self.assertIn(".elms-pulse-dot", css)
        self.assertIn(".elms-timer-value", css)

    def test_learning_js_standard_page_and_telemetry(self):
        """JS must register elms-learning page and bind anti-cheat heartbeat."""
        js = self.js_path.read_text(encoding="utf-8")
        self.assertIn('frappe.standard_pages[pageName]', js)
        self.assertIn('elms.lms.api.get_learner_dashboard', js)
        self.assertIn('elms.lms.api.get_learning_admin_data', js)
        self.assertIn('Управление LMS', js)
        self.assertIn('Создать курс', js)
        self.assertIn('Оформить зачисление', js)
        self.assertIn('ELMS Course Chapter', js)
        self.assertIn('elms.lms.api.record_lesson_progress', js)
        self.assertIn('window.addEventListener("blur"', js)
        self.assertIn('window.addEventListener("focus"', js)
        self.assertIn('heartbeatInterval', js)

    def test_lms_workspace_exposes_learning_cabinet_shortcut(self):
        """Workspace LMS must provide shortcut to /app/elms-learning."""
        from elms.desk.workspaces import ELMS_WORKSPACE_DEFINITIONS
        lms_ws = next((item for item in ELMS_WORKSPACE_DEFINITIONS if item["name"] == "LMS"), None)
        self.assertIsNotNone(lms_ws)
        shortcuts = lms_ws.get("shortcuts", ())
        urls = [sc.get("url") for sc in shortcuts]
        self.assertIn("/app/elms-learning", urls)


if __name__ == "__main__":
    unittest.main()
