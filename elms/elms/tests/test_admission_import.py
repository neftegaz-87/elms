from __future__ import annotations

import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import frappe

from elms.admission import import_api, import_service
from elms.admission.credentials import synthetic_identity
from elms.admission.import_schemas import (
    SCHEMA_VERSION,
    AdmissionAIResponse,
    AdmissionHeader,
    AdmissionImportStatus,
)


ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT.parent / "memory-bank" / "app" / "clarify" / "fixtures-20261116-admission"


def ai_provider(workbook, organization):
    return (
        AdmissionAIResponse(
            schema_version=SCHEMA_VERSION,
            header=AdmissionHeader(
                organization_name="ООО ЛНК ПРЕМИУМ",
                inn="8603253461",
                program_title="РПО",
                training_kind="повышение квалификации",
            ),
            rows=[
                {
                    "source_row_number": 15,
                    "fio": "Сметанин Виктор Валерьевич",
                    "profession": "Дефектоскопист",
                    "birth_date": "1983-06-02",
                    "snils": "125-609-984 78",
                    "education": "среднее профессиональное",
                    "phone": "",
                    "contractor": "ООО ЛНК ПРЕМИУМ",
                    "program": "РПО",
                    "training_kind": "повышение квалификации",
                    "email": "",
                }
            ],
        ),
        "provider-cid",
    )


class TestAdmissionImportSchemas(unittest.TestCase):
    def test_sample_fixture_maps_header_and_smetanin_row_before_ai_validation(self):
        content = (FIXTURES / "sample-rpo-smetanin.xlsx").read_bytes()

        workbook = import_service.extract_workbook(content)

        self.assertEqual(workbook.header["organization_name"], 'ООО "ЛНК ПРЕМИУМ"')
        self.assertEqual(workbook.header["inn"], "8603253461")
        self.assertEqual(workbook.rows[0]["fio"], "Сметанин Виктор Валерьевич")
        self.assertEqual(workbook.rows[0]["snils"], "125-609-984 78")
        self.assertEqual(workbook.rows[0]["birth_date"], "1983-06-02")

    def test_grounded_response_is_typed_and_valid(self):
        content = (FIXTURES / "sample-rpo-smetanin.xlsx").read_bytes()

        result = import_service.parse_workbook(content, organization="ORG-1", provider=ai_provider)

        self.assertEqual(result.status, AdmissionImportStatus.PARSED)
        self.assertEqual(result.rows[0].fio, "Сметанин Виктор Валерьевич")
        self.assertEqual(result.rows[0].snils, "12560998478")
        self.assertEqual(result.correlation_id, "provider-cid")

    def test_invalid_row_fails_closed_with_row_error(self):
        def invalid_provider(workbook, organization):
            response, correlation_id = ai_provider(workbook, organization)
            values = response.rows[0].copy()
            values["snils"] = "123"
            return response.model_copy(update={"rows": [values]}), correlation_id

        content = (FIXTURES / "sample-rpo-smetanin.xlsx").read_bytes()

        result = import_service.parse_workbook(content, provider=invalid_provider)

        self.assertEqual(result.status, AdmissionImportStatus.FAILED)
        self.assertEqual(result.rows, [])
        self.assertEqual(result.failures[0].source_row_number, 15)
        self.assertIn("СНИЛС", result.failures[0].errors[0])

    def test_corrupt_xlsx_is_explicit_failure_and_provider_is_not_called(self):
        provider = MagicMock(side_effect=AssertionError("corrupt input must fail before AI"))

        result = import_service.parse_workbook(b"not an xlsx", provider=provider)

        self.assertEqual(result.status, AdmissionImportStatus.FAILED)
        self.assertTrue(result.error)
        provider.assert_not_called()

    def test_synthetic_login_and_email_are_deterministic_but_token_is_secret(self):
        first = synthetic_identity("ORG-1", "Сметанин Виктор Валерьевич", "12560998478")
        second = synthetic_identity("ORG-1", "Сметанин Виктор Валерьевич", "12560998478")

        self.assertEqual(first.login, second.login)
        self.assertEqual(first.email, second.email)
        self.assertNotEqual(first.invite_token, second.invite_token)
        self.assertNotIn(first.invite_token, first.email)


class TestAdmissionImportAPI(unittest.TestCase):
    def test_company_admin_cannot_upload_foreign_organization(self):
        with (
            patch.object(import_api.frappe, "session", SimpleNamespace(user="company@example.test"), create=True),
            patch.object(import_api.frappe, "get_roles", return_value=["ELMS Company Admin"], create=True),
            patch.object(import_api, "is_company_admin", return_value=True),
            patch.object(import_api, "is_platform_admin", return_value=False),
            patch.object(import_api, "organizations_for_user", return_value=["ORG-OWN"]),
            patch.object(import_api, "require_organization_mutation_access", return_value="ORG-OWN"),
        ):
            with self.assertRaises(frappe.PermissionError):
                import_api.upload_import(
                    "admission.xlsx",
                    "UEsDBA==",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    organization="ORG-FOREIGN",
                )

    def test_upload_uses_real_service_and_keeps_revision_flag(self):
        with (
            patch.object(import_api.frappe, "session", SimpleNamespace(user="company@example.test"), create=True),
            patch.object(import_api.frappe, "get_roles", return_value=["ELMS Company Admin"], create=True),
            patch.object(import_api, "is_company_admin", return_value=True),
            patch.object(import_api, "is_platform_admin", return_value=False),
            patch.object(import_api, "organizations_for_user", return_value=["ORG-OWN"]),
            patch.object(import_api, "require_organization_mutation_access", return_value="ORG-OWN"),
            patch.object(import_api, "persist_import", return_value={"name": "ADMISSION-1"}) as persist,
            patch.object(import_api, "validate_upload"),
        ):
            result = import_api.upload_import(
                "admission.xlsx",
                "UEsDBA==",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                organization="ORG-OWN",
                new_revision=True,
            )

        self.assertEqual(result["name"], "ADMISSION-1")
        self.assertEqual(persist.call_args.kwargs["organization"], "ORG-OWN")
        self.assertTrue(persist.call_args.kwargs["new_revision"])

    def test_import_boundary_has_no_forbidden_downstream_calls(self):
        for path in (
            ROOT / "elms" / "admission" / "import_api.py",
            ROOT / "elms" / "admission" / "import_service.py",
            ROOT / "elms" / "admission" / "credentials.py",
        ):
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("Enrollment", text)
            self.assertNotIn("enroll_", text)


if __name__ == "__main__":
    unittest.main()
