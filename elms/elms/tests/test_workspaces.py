"""Contracts for the ELMS role-filtered Desk navigation."""

import unittest
from unittest.mock import MagicMock, patch

import frappe
from elms.desk.workspaces import (
    ELMS_WORKSPACE_DEFINITIONS,
    HIDDEN_PLATFORM_WORKSPACES,
    OBSOLETE_ELMS_WORKSPACES,
    _workspace_content,
    ensure_workspaces,
    filter_workspace_for_user,
)


class TestELMSWorkspaces(unittest.TestCase):
    def test_workspace_roles_and_lms_first_order_are_product_roles(self):
        self.assertEqual([item["name"] for item in ELMS_WORKSPACE_DEFINITIONS], ["LMS", "Предпросмотр курсов", "Settings"])
        self.assertEqual(
            ELMS_WORKSPACE_DEFINITIONS[0]["roles"],
            (
                "ELMS Admin",
                "ELMS Operations User",
                "ELMS Learner",
                "ELMS Instructor",
                "ELMS Methodologist",
            ),
        )
        self.assertEqual(
            ELMS_WORKSPACE_DEFINITIONS[1]["roles"],
            ("ELMS Admin", "ELMS Operations User", "ELMS Instructor", "ELMS Methodologist"),
        )
        self.assertEqual(ELMS_WORKSPACE_DEFINITIONS[2]["roles"], ("ELMS Admin", "System Manager"))

    def test_lms_workspace_uses_canonical_elms_display_label(self):
        self.assertEqual(ELMS_WORKSPACE_DEFINITIONS[0]["label"], "elms")
        self.assertNotIn("ELMS СДО", ELMS_WORKSPACE_DEFINITIONS[0]["content"])

    def test_lms_workspace_exposes_assessment_doctypes(self):
        lms = next(item for item in ELMS_WORKSPACE_DEFINITIONS if item["name"] == "LMS")
        links = {(link_to, label) for _, link_to, label in lms["links"]}
        self.assertIn(("ELMS Course", "Курсы"), links)
        self.assertNotIn(("ELMS Course Lesson", "Уроки и материалы"), links)
        self.assertIn(("ELMS Quiz", "Тесты и экзамены"), links)
        self.assertIn(("ELMS Quiz Question", "Банк вопросов"), links)
        self.assertIn(("ELMS Course Progress", "Прогресс по курсам"), links)

    def test_lms_workspace_is_shared_but_role_gated(self):
        learner = next(item for item in ELMS_WORKSPACE_DEFINITIONS if item["name"] == "LMS")
        self.assertIn("ELMS Learner", learner["roles"])

    def test_preview_workspace_is_role_gated_and_has_a_learner_preview_route(self):
        preview = next(item for item in ELMS_WORKSPACE_DEFINITIONS if item["name"] == "Предпросмотр курсов")
        self.assertEqual(preview["label"], "Предпросмотр курсов")
        self.assertNotIn("ELMS Learner", preview["roles"])
        self.assertEqual(preview["shortcuts"][0]["url"], "/app/elms-course-preview")
        content = _workspace_content(preview["content"], preview["links"], preview["shortcuts"])
        self.assertIn('"type": "shortcut"', content)
        self.assertIn("Открыть предпросмотр", content)

    def test_review_workspace_exposes_the_permission_anchor_and_handoff(self):
        self.assertNotIn("Operations", [item["name"] for item in ELMS_WORKSPACE_DEFINITIONS])
        self.assertNotIn("Review", [item["name"] for item in ELMS_WORKSPACE_DEFINITIONS])

    def test_platform_workspaces_are_explicitly_removed_from_navigation(self):
        for name in ("Website", "Tools", "Integrations", "Build"):
            self.assertIn(name, HIDDEN_PLATFORM_WORKSPACES)

    def test_obsolete_management_workspace_is_removed_from_navigation(self):
        self.assertEqual(OBSOLETE_ELMS_WORKSPACES, ("Управление LMS", "Operations", "Review"))

    def test_ensure_is_idempotent_and_fails_when_platform_workspace_is_missing(self):
        db = MagicMock()
        db.exists.side_effect = lambda doctype, name: doctype == "Workspace" and name in {
            item["name"] for item in ELMS_WORKSPACE_DEFINITIONS
        }
        workspace = MagicMock()
        workspace.is_new.return_value = False
        with (
            patch.object(frappe, "db", db, create=True),
            patch.object(frappe, "get_doc", return_value=workspace, create=True),
            patch.object(frappe, "throw", side_effect=RuntimeError, create=True),
        ):
            with self.assertRaises(RuntimeError):
                ensure_workspaces()

    def test_learner_gets_the_shared_lms_workspace_without_management_links(self):
        page = {"links": _workspace_links_for_test(), "content": _workspace_content("LMS", ELMS_WORKSPACE_DEFINITIONS[0]["links"], ELMS_WORKSPACE_DEFINITIONS[0]["shortcuts"])}
        with patch.object(frappe, "get_roles", return_value=["ELMS Learner"], create=True):
            filter_workspace_for_user(page, "LMS", "learner@example.test")
        self.assertEqual([link for link in page["links"] if link.get("type") == "Link"], [])
        self.assertNotIn("Конструктор курсов", page["content"])

    def test_methodologist_gets_course_studio_shortcut(self):
        page = {
            "links": _workspace_links_for_test(),
            "shortcuts": list(ELMS_WORKSPACE_DEFINITIONS[0]["shortcuts"]),
            "content": _workspace_content("LMS", ELMS_WORKSPACE_DEFINITIONS[0]["links"], ELMS_WORKSPACE_DEFINITIONS[0]["shortcuts"]),
        }
        with patch.object(frappe, "get_roles", return_value=["ELMS Methodologist"], create=True):
            filter_workspace_for_user(page, "LMS", "methodologist@example.test")
        self.assertIn("/app/elms-course-studio", [shortcut.get("url") for shortcut in page["shortcuts"]])


def _workspace_links_for_test():
    from elms.desk.workspaces import _workspace_links

    return _workspace_links(ELMS_WORKSPACE_DEFINITIONS[0])


if __name__ == "__main__":
    unittest.main()
