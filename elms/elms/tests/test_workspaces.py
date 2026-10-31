"""Contracts for the ELMS role-filtered Desk navigation."""

import unittest
from unittest.mock import MagicMock, patch

import frappe
from elms.desk.workspaces import (
    ELMS_WORKSPACE_DEFINITIONS,
    HIDDEN_PLATFORM_WORKSPACES,
    ensure_workspaces,
)


class TestELMSWorkspaces(unittest.TestCase):
    def test_workspace_roles_and_lms_first_order_are_product_roles(self):
        self.assertEqual([item["name"] for item in ELMS_WORKSPACE_DEFINITIONS], ["LMS", "Operations", "Settings"])
        self.assertEqual(ELMS_WORKSPACE_DEFINITIONS[0]["roles"], ("ELMS Admin", "ELMS LMS User"))
        self.assertEqual(ELMS_WORKSPACE_DEFINITIONS[1]["roles"], ("ELMS Admin", "ELMS Operations User"))
        self.assertEqual(ELMS_WORKSPACE_DEFINITIONS[2]["roles"], ("ELMS Admin",))

    def test_operations_workspace_exposes_guarded_review_handoff(self):
        operations = next(item for item in ELMS_WORKSPACE_DEFINITIONS if item["name"] == "Operations")
        assert operations["shortcuts"] == (
            {
                "type": "URL",
                "url": "/app/elms-review",
                "label": "Сверка заявки",
                "icon": "check-circle",
            },
        )

    def test_platform_workspaces_are_explicitly_removed_from_navigation(self):
        for name in ("Website", "Tools", "Integrations", "Build"):
            self.assertIn(name, HIDDEN_PLATFORM_WORKSPACES)

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


if __name__ == "__main__":
    unittest.main()
