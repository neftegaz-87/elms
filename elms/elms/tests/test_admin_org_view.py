"""Contracts for the platform organization-view read-only boundary."""

from __future__ import annotations

import unittest
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import frappe

if "frappe.model.document" not in sys.modules:
    frappe_model = sys.modules.setdefault("frappe.model", __import__("types").ModuleType("frappe.model"))
    frappe_document = __import__("types").ModuleType("frappe.model.document")
    frappe_document.Document = object
    sys.modules["frappe.model.document"] = frappe_document
    setattr(frappe_model, "document", frappe_document)

from elms.access import api as access_api
from elms.admission import import_api
from elms.cabinet import roster
import elms.lms.api as lms_api
from elms.lms.services.b2b_admission import B2BAdmissionService, AdmissionPolicyError


class TestAdminOrganizationView(unittest.TestCase):
    def test_operations_user_receives_all_organizations_as_read_only_context(self):
        with (
            patch.object(access_api, "_current_user", return_value="ops@example.test"),
            patch.object(access_api, "_roles", return_value={"ELMS Operations User"}),
            patch.object(access_api, "_is_admin", return_value=False),
            patch.object(
                access_api.frappe,
                "get_all",
                return_value=[{"name": "ORG-A"}, {"name": "ORG-B"}],
                create=True,
            ),
        ):
            result = access_api.get_company_access_context()

        self.assertEqual(result["organizations"], ["ORG-A", "ORG-B"])
        self.assertTrue(result["platform_viewer"])
        self.assertTrue(result["read_only"])
        self.assertFalse(result["platform_admin"])

    def test_company_admin_context_stays_membership_scoped(self):
        with (
            patch.object(access_api, "_current_user", return_value="company@example.test"),
            patch.object(access_api, "_roles", return_value={"ELMS Company Admin"}),
            patch.object(access_api, "_is_admin", return_value=False),
            patch.object(access_api, "_organizations_for_user", return_value=["ORG-OWN"]),
            patch.object(access_api, "_company_roles", return_value=[]),
        ):
            result = access_api.get_company_access_context()

        self.assertEqual(result["organizations"], ["ORG-OWN"])
        self.assertEqual(result["organization"], "ORG-OWN")
        self.assertFalse(result["platform_viewer"])
        self.assertFalse(result["read_only"])

    def test_platform_viewer_can_read_but_cannot_mutate_selected_organization(self):
        with (
            patch.object(access_api, "_roles", return_value={"ELMS Operations User"}),
            patch.object(access_api, "organization_membership_exists", return_value=False),
        ):
            self.assertEqual(
                access_api.require_organization_access("ORG-A", "ops@example.test"),
                "ORG-A",
            )
            with self.assertRaises(frappe.PermissionError):
                access_api.require_organization_mutation_access("ORG-A", "ops@example.test")

    def test_roster_view_records_existing_activity_event_after_authorized_read(self):
        activity = MagicMock()

        def get_all(doctype, **kwargs):
            if doctype == "ELMS Organization Member":
                return [{"user": "learner@example.test", "role_profile": "ELMS Learner Profile"}]
            if doctype == "User":
                return [{"name": "learner@example.test", "email": "learner@example.test", "enabled": 1}]
            if doctype == "ELMS Enrollment":
                return []
            if doctype == "ELMS Course Progress":
                return []
            raise AssertionError(f"Unexpected doctype: {doctype}")

        with (
            patch.object(roster, "_current_user", return_value="ops@example.test"),
            patch.object(roster, "_organization_exists", return_value=True),
            patch.object(roster, "require_organization_access", return_value="ORG-A"),
            patch.object(roster.frappe, "get_all", side_effect=get_all, create=True),
            patch.object(roster, "_member_count", return_value=1),
            patch.object(roster.frappe, "get_doc", return_value=activity, create=True),
        ):
            result = roster.build_org_roster("ORG-A")

        self.assertEqual(result["organization"], "ORG-A")
        activity.insert.assert_called_once_with(ignore_permissions=True)
        self.assertEqual(activity.activity_type, "Organization View")
        self.assertEqual(activity.organization, "ORG-A")
        self.assertEqual(activity.user, "ops@example.test")
        self.assertEqual(activity.reference_doctype, "ELMS Organization")
        self.assertEqual(activity.reference_name, "ORG-A")

    def test_operations_user_cannot_upload_import(self):
        with (
            patch.object(import_api, "_current_user", return_value="ops@example.test"),
            patch.object(import_api, "is_platform_admin", return_value=False),
            patch.object(import_api, "is_company_admin", return_value=False),
            patch.object(import_api, "_is_operations_user", return_value=True),
        ):
            with self.assertRaises(frappe.PermissionError):
                import_api._resolve_organization("ORG-A", write=True)

    def test_platform_operations_user_cannot_enroll_another_user(self):
        with (
            patch.object(lms_api, "_get_current_user", return_value="ops@example.test"),
            patch.object(
                lms_api,
                "_has_role",
                side_effect=lambda role, user=None: role == "ELMS Operations User",
            ),
            patch.object(lms_api.frappe, "get_roles", return_value=["ELMS Operations User"], create=True),
        ):
            with self.assertRaises(frappe.PermissionError):
                lms_api.enroll_learner(user="learner@example.test", batch="BATCH-A")

    def test_b2b_service_rejects_platform_viewer_before_import_load(self):
        service = B2BAdmissionService(user="ops@example.test", organization="ORG-A")
        with patch.object(
            service,
            "_actor_organization",
            return_value="ORG-A",
        ):
            with patch.object(
                service,
                "_load_owned_parsed_import",
                side_effect=AdmissionPolicyError("ACTOR_ROLE_FORBIDDEN", "read only"),
            ):
                with self.assertRaises(AdmissionPolicyError) as error:
                    service.confirm("IMP-A")

        self.assertEqual(error.exception.code, "ACTOR_ROLE_FORBIDDEN")

    def test_desk_surfaces_use_server_selector_and_read_only_copy(self):
        cabinet_js = open("elms/elms/public/js/desk-cabinet.js", encoding="utf-8").read()
        admission_js = open("elms/elms/public/js/desk-admission.js", encoding="utf-8").read()
        access_js = open("elms/elms/public/js/desk-access.js", encoding="utf-8").read()

        self.assertIn("get_company_access_context", cabinet_js)
        self.assertIn("data-cabinet-organization", cabinet_js)
        self.assertNotIn("Введите организацию для просмотра", cabinet_js)
        self.assertIn("режим просмотра", cabinet_js)
        self.assertIn("режим просмотра", admission_js)
        self.assertIn("режим просмотра", access_js)


if __name__ == "__main__":
    unittest.main()
