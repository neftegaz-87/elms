"""Contract tests for public application submission."""

from __future__ import annotations

import json
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import frappe

from elms.applications import api
from elms.applications.bitrix_leads import BitrixLeadCreateError, build_lead_params
from elms.applications.schemas import ApplicationSubmitPayload


class FakeLink(SimpleNamespace):
    def insert(self, **kwargs):
        self.name = "APP-LINK-1"
        return self


def individual_payload(**overrides):
    payload = {
        "application_kind": "individual",
        "fio": "Иван Петров",
        "email": "ivan@example.test",
        "phone": "+79990000000",
        "course": "COURSE-1",
        "course_ids": [],
        "consent": True,
        "website": "",
    }
    payload.update(overrides)
    return payload


def legal_payload(**overrides):
    payload = {
        "application_kind": "legal",
        "company_name": "ООО Пример",
        "inn": "7701234567",
        "contact_fio": "Анна Сидорова",
        "email": "anna@example.test",
        "phone": "+79991112233",
        "course_ids": ["COURSE-1", "COURSE-2"],
        "comment": "Нужна корпоративная группа",
        "consent": True,
        "website": "",
    }
    payload.update(overrides)
    return payload


class TestApplicationSchemas(unittest.TestCase):
    def test_individual_and_legal_payloads_are_typed(self):
        individual = ApplicationSubmitPayload.model_validate(individual_payload())
        legal = ApplicationSubmitPayload.model_validate(legal_payload())

        self.assertEqual(individual.application_kind, "individual")
        self.assertEqual(legal.course_ids, ["COURSE-1", "COURSE-2"])

    def test_consent_and_honeypot_are_required_to_be_clean(self):
        with self.assertRaises(ValueError):
            ApplicationSubmitPayload.model_validate(individual_payload(consent=False))
        with self.assertRaises(ValueError):
            ApplicationSubmitPayload.model_validate(individual_payload(website="bot"))


class TestBitrixLeadMapping(unittest.TestCase):
    def test_individual_mapping_uses_crm_lead_fields(self):
        params = build_lead_params(ApplicationSubmitPayload.model_validate(individual_payload()))

        self.assertEqual(params["fields"]["TITLE"], "Заявка на курс ELMS: COURSE-1")
        self.assertEqual(params["fields"]["EMAIL"][0]["VALUE"], "ivan@example.test")
        self.assertNotIn("crm.deal.add", json.dumps(params))

    def test_legal_mapping_contains_company_and_inn(self):
        params = build_lead_params(ApplicationSubmitPayload.model_validate(legal_payload()))

        self.assertEqual(params["fields"]["COMPANY_TITLE"], "ООО Пример")
        self.assertIn("7701234567", params["fields"]["COMMENTS"])


class TestApplicationSubmit(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()
        self.db.exists.return_value = False
        self.link = FakeLink()

    def _get_doc(self, values):
        if isinstance(values, dict):
            self.link.__dict__.update(values)
        return self.link

    def test_individual_submit_creates_bitrix_link_and_tracking_ref(self):
        with (
            patch.object(frappe, "db", self.db, create=True),
            patch.object(frappe, "get_all", return_value=[{"name": "COURSE-1"}], create=True),
            patch.object(frappe, "get_doc", side_effect=self._get_doc, create=True),
            patch.object(api, "create_bitrix_lead", return_value="42"),
        ):
            result = api.submit_application(json.dumps(individual_payload()))

        self.assertEqual(result["bitrix_id"], "42")
        self.assertEqual(result["tracking_ref"], "APP-LINK-1")
        self.assertEqual(self.link.bitrix_id, "42")
        self.assertEqual(self.link.application_kind, "individual")

    def test_legal_submit_persists_multi_course_application(self):
        with (
            patch.object(frappe, "db", self.db, create=True),
            patch.object(frappe, "get_all", return_value=[{"name": "COURSE-1"}, {"name": "COURSE-2"}], create=True),
            patch.object(frappe, "get_doc", side_effect=self._get_doc, create=True),
            patch.object(api, "create_bitrix_lead", return_value="84"),
        ):
            result = api.submit_application(legal_payload())

        self.assertEqual(result["application_kind"], "legal")
        self.assertEqual(self.link.course_ids, ["COURSE-1", "COURSE-2"])
        self.assertEqual(self.link.company_name, "ООО Пример")

    def test_bitrix_failure_never_returns_success_or_creates_link(self):
        with (
            patch.object(frappe, "db", self.db, create=True),
            patch.object(frappe, "get_all", return_value=[{"name": "COURSE-1"}], create=True),
            patch.object(frappe, "get_doc", side_effect=self._get_doc, create=True),
            patch.object(api, "create_bitrix_lead", side_effect=BitrixLeadCreateError("down")),
        ):
            with self.assertRaises(frappe.ValidationError):
                api.submit_application(individual_payload())

        self.assertFalse(hasattr(self.link, "name"))

    def test_only_rest_webhook_configuration_is_accepted(self):
        with patch.dict("os.environ", {"BITRIX_WEBHOOK_URL": "https://board.example/key"}, clear=True):
            with patch("elms.applications.bitrix_leads.post_json") as post_json:
                with self.assertRaises(BitrixLeadCreateError):
                    from elms.applications.bitrix_leads import create_bitrix_lead

                    create_bitrix_lead(ApplicationSubmitPayload.model_validate(individual_payload()))
        post_json.assert_not_called()


if __name__ == "__main__":
    unittest.main()
