import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


class TestDeskBranding(unittest.TestCase):
    def test_desk_shell_uses_installed_elms_app_title(self):
        source = (REPO_ROOT / "frappe/frappe/public/js/frappe/ui/desk_sidebar_chrome.js").read_text(
            encoding="utf-8"
        )

        self.assertNotIn("ERP CRM", source)
        self.assertIn("frappe.boot?.apps_data?.apps", source)
        self.assertIn('app.name === "elms"', source)
        self.assertIn("app?.title", source)

    def test_desk_uses_elms_visual_tokens_and_workspace_scope(self):
        tokens = (REPO_ROOT / "design-system/tokens.css").read_text(encoding="utf-8")
        shell = (REPO_ROOT / "design-system/shell-desk.css").read_text(encoding="utf-8")

        self.assertIn("--ds-accent: #0d4cd3", tokens)
        self.assertIn("--ds-font-family: \"Source Sans 3\"", tokens)
        self.assertNotIn("fonts.googleapis.com", tokens)
        self.assertIn("/assets/elms/fonts/source-sans-3-cyrillic-400-normal.woff2", tokens)
        self.assertIn("--ds-radius-sm: 3px", tokens)
        self.assertIn("--ds-space-1: 4px", tokens)
        self.assertIn(".ds-workspace", shell)
        self.assertNotIn(".ds-crm-workspace", shell)
        self.assertNotIn("transition: margin-left", shell)
        self.assertNotIn("transition: width 150ms", shell)

    def test_workspace_surface_does_not_depend_on_missing_route_attribute(self):
        source = (REPO_ROOT / "frappe/frappe/public/js/frappe/ui/desk_sidebar_chrome.js").read_text(
            encoding="utf-8"
        )

        self.assertIn('.find(".editor-js-container, #editorjs")', source)
        self.assertIn('toggleClass("ds-workspace", is_workspace_route)', source)


if __name__ == "__main__":
    unittest.main()
