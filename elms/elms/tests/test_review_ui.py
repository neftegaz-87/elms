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
        self.assertIn('frappe.standard_pages[reviewPageName]', self.js)
        self.assertIn('frame.src = reviewEndpoint', self.js)
        self.assertIn('shell.className = "elms-review-shell"', self.js)
        self.assertIn('wrapper.append(shell)', self.js)
        self.assertIn('frappe.set_route(reviewPageName)', self.js)
        self.assertNotIn("window.location.assign(reviewHref)", self.js)

    def test_review_surface_is_sized_inside_the_main_desk_column(self):
        self.assertIn("app_include_css", self.hooks)
        self.assertIn("/assets/elms/css/desk-review.css", self.hooks)
        self.assertIn(".elms-review-page .layout-main-section", self.css)
        self.assertIn(".elms-review-page-main", self.css)
        self.assertIn(".elms-review-shell", self.css)
        self.assertIn('body[data-route="elms-review"] #body', self.css)
        review_page_rule = self.css.split(".elms-review-page {", 1)[1].split("}", 1)[0]
        self.assertIn("display: block;", review_page_rule)
        self.assertNotIn("display: block !important", review_page_rule)
        self.assertIn("position: fixed", self.css)
        self.assertIn("left: var(--ds-desk-rail-width, 0px)", self.css)
        self.assertIn(".elms-review-page .page-head", self.css)
        self.assertIn("display: none", self.css)
        self.assertIn("overflow: hidden", self.css)
        self.assertIn("min-height: 0", self.css)
        self.assertNotIn("min-height: 640px", self.css)
        self.assertIn(".elms-review-page .elms-review-frame", self.css)
        self.assertIn('frame.setAttribute("scrolling", "no")', self.js)


if __name__ == "__main__":
    unittest.main()
