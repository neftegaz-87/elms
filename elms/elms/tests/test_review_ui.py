"""Contracts for opening the review service inside the ELMS Desk shell."""

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


class TestReviewUI(unittest.TestCase):
    def setUp(self):
        self.js = (REPO_ROOT / "elms/elms/public/js/desk-review.js").read_text(encoding="utf-8")
        self.css = (REPO_ROOT / "elms/elms/public/css/desk-review.css").read_text(encoding="utf-8")
        self.hooks = (REPO_ROOT / "elms/elms/hooks.py").read_text(encoding="utf-8")

    def test_review_uses_a_desk_route_and_embeds_the_service(self):
        self.assertIn('reviewPageName = "elms-review"', self.js)
        self.assertIn("elms_review_visible", self.js)
        self.assertIn("function isReviewVisible()", self.js)
        self.assertIn('frappe.standard_pages[reviewPageName]', self.js)
        self.assertIn('frame.src = reviewEndpoint', self.js)
        self.assertIn('shell.className = "elms-review-shell"', self.js)
        self.assertIn('wrapper.append(shell)', self.js)
        self.assertIn('frappe.set_route(reviewPageName)', self.js)
        self.assertNotIn("window.location.assign(reviewHref)", self.js)

    def test_review_surface_is_not_added_to_the_lms_desk_navigation(self):
        self.assertIn("app_include_css", self.hooks)
        self.assertNotIn("/assets/elms/css/desk-review.css", self.hooks)
        self.assertNotIn("/assets/elms/js/desk-review.js", self.hooks)

    def test_review_visibility_is_part_of_the_boot_and_workspace_contract(self):
        self.assertIn("extend_bootinfo", self.hooks)
        self.assertIn("elms.sso.review.extend_bootinfo", self.hooks)
        self.assertIn("override_whitelisted_methods", self.hooks)
        self.assertIn("elms.sso.review.get_desktop_page", self.hooks)

    def test_apps_screen_has_logos_and_permission_gated_review_card(self):
        self.assertIn('"logo": "/assets/elms/images/nftgz-favicon.svg"', self.hooks)
        self.assertNotIn('"route": "/app/review"', self.hooks)


if __name__ == "__main__":
    unittest.main()
