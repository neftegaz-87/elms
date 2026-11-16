"""Contracts for company-scoped integrations and secret-safe API responses."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import frappe

from elms.integrations import api
from elms import tenant


ROOT = Path(__file__).resolve().parents[1]


class TestCompanyIntegrationSchema(unittest.TestCase):
	def test_company_integration_page_is_wired_for_company_admin(self):
		page = json.loads((ROOT / "operations" / "page" / "elms_company_integrations" / "elms_company_integrations.json").read_text(encoding="utf-8"))
		roles = {item["role"] for item in page["roles"]}
		self.assertEqual(roles, {"ELMS Admin", "ELMS Company Admin"})
		hooks = (ROOT / "hooks.py").read_text(encoding="utf-8")
		js = (ROOT / "public" / "js" / "desk-company-integrations.js").read_text(encoding="utf-8")
		self.assertIn("elms-company-integrations", hooks)
		self.assertIn("elms.integrations.api.get_organization_integrations", js)
		self.assertIn("elms.integrations.api.save_organization_integration", js)
		self.assertIn("elms.integrations.api.delete_organization_integration", js)

	def test_tenant_permission_denies_foreign_company_document(self):
		doc = SimpleNamespace(doctype="ELMS Organization Integration", organization="Foreign")
		with (
			patch.object(tenant, "is_platform_admin", return_value=False),
			patch.object(tenant, "organizations_for_user", return_value=["Acme"]),
		):
			self.assertFalse(tenant.has_tenant_permission(doc, user="company@example.test", permission_type="read"))

	def test_tenant_permission_denies_foreign_member_document(self):
		doc = SimpleNamespace(doctype="ELMS Organization Member", organization="Foreign")
		with (
			patch.object(tenant, "is_platform_admin", return_value=False),
			patch.object(tenant, "organizations_for_user", return_value=["Acme"]),
		):
			self.assertFalse(tenant.has_tenant_permission(doc, user="company@example.test", permission_type="read"))

	def test_doctype_is_company_scoped_and_secret_fields_are_passwords(self):
		path = ROOT / "elms_core" / "doctype" / "elms_organization_integration" / "elms_organization_integration.json"
		payload = json.loads(path.read_text(encoding="utf-8"))
		self.assertEqual(payload["name"], "ELMS Organization Integration")
		fields = {item["fieldname"]: item for item in payload["fields"]}
		self.assertEqual(fields["organization"]["options"], "ELMS Organization")
		self.assertEqual(fields["api_key"]["fieldtype"], "Password")
		self.assertEqual(fields["webhook_url"]["fieldtype"], "Password")
		roles = {item["role"] for item in payload["permissions"] if item.get("write")}
		self.assertIn("ELMS Admin", roles)
		self.assertIn("ELMS Company Admin", roles)

	def test_api_dto_never_returns_secret_values(self):
		doc = SimpleNamespace(
		name="integration-1",
		organization="Acme",
		integration_type="LLM",
		enabled=1,
		base_url="https://llm.acme.test/v1",
		default_model="acme-model",
		config_json="{}",
		get_password=lambda field: "secret-value" if field == "api_key" else "",
		api_key="",
		webhook_url="",
		flags=SimpleNamespace(),
		is_new=lambda: False,
	)
		row = api._as_row(doc)
		self.assertNotIn("secret-value", row.values())
		self.assertTrue(row["api_key_configured"])
		self.assertNotIn("api_key", row)

	def test_company_admin_context_cannot_select_foreign_organization(self):
		with patch.object(api, "require_organization_access", side_effect=frappe.PermissionError("denied")):
			with self.assertRaises(frappe.PermissionError):
				api.get_organization_integrations("Foreign")

	def test_company_integration_navigation_has_one_overview_and_three_detail_pages(self):
		hooks = (ROOT / "hooks.py").read_text(encoding="utf-8")
		page_js = (ROOT / "public" / "js" / "elms-company-integrations-page.js").read_text(encoding="utf-8")
		integration_js = (ROOT / "public" / "js" / "desk-company-integrations.js").read_text(encoding="utf-8")
		self.assertIn('"elms-company-integration-llm"', hooks)
		self.assertIn('"elms-company-integration-bitrix24"', hooks)
		self.assertIn('"elms-company-integration-custom-api"', hooks)
		self.assertIn('"elms-company-integrations": ""', page_js)
		self.assertIn('"elms-company-integration-llm": "LLM"', page_js)
		self.assertIn('Object.prototype.hasOwnProperty.call(pageTypes, currentPage)', page_js)
		self.assertIn('data-company-integrations-route', integration_js)
		self.assertIn('delete frappe.pages[route]', integration_js)
		self.assertIn('frappe.set_route(route)', integration_js)
		workspace = (ROOT / "desk" / "workspaces.py").read_text(encoding="utf-8")
		self.assertEqual(workspace.count('"label": "Интеграции компании"'), 1)

	def test_tenant_query_conditions_qualify_current_table_columns(self):
		with (
			patch.object(tenant, "is_platform_admin", return_value=False),
			patch.object(tenant, "organizations_for_user", return_value=["Acme"]),
		):
			condition = tenant.get_permission_query_conditions("company@example.test", "ELMS Organization Member")
		self.assertIn("`tabELMS Organization Member`.`organization`", condition)
		self.assertFalse(condition.startswith("`organization`"))

	def test_config_json_requires_valid_json(self):
		with self.assertRaises(frappe.ValidationError):
			api._clean_config("not-json")
		self.assertEqual(api._clean_config({"region": "ru"}), '{"region": "ru"}')


class TestCompanyIntegrationWriteContract(unittest.TestCase):
	def test_save_preserves_existing_secret_when_form_field_is_blank(self):
		doc = MagicMock()
		doc.name = "integration-1"
		doc.organization = "Acme"
		doc.integration_type = "LLM"
		doc.enabled = 1
		doc.base_url = "https://llm.acme.test/v1"
		doc.default_model = "model"
		doc.config_json = "{}"
		doc.api_key = ""
		doc.webhook_url = ""
		doc.get_password.side_effect = lambda field: "saved-secret" if field == "api_key" else ""
		doc.is_new.return_value = False
		doc.flags = SimpleNamespace()
		doc.save.return_value = doc
		with (
			patch.object(api, "_organization", return_value="Acme"),
			patch.object(api, "_find", return_value=doc),
		):
			result = api.save_organization_integration(
				organization="Acme",
				integration_type="LLM",
				enabled=1,
				base_url="https://llm.acme.test/v1",
				default_model="model",
			)
		self.assertEqual(result["organization"], "Acme")
		self.assertEqual(doc.api_key, "")
		doc.save.assert_called_once_with(ignore_permissions=True)


if __name__ == "__main__":
	unittest.main()
