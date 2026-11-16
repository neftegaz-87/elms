"""Contracts for per-organization provider resolution."""

from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import frappe

from elms.ai import omniroute
from elms.integrations import bitrix_config, resolver


class TestOrganizationResolution(unittest.TestCase):
	def test_company_context_resolves_only_its_organization(self):
		with (
			patch.object(resolver, "is_platform_admin", return_value=False),
			patch.object(resolver, "organizations_for_user", return_value=["Acme"]),
			patch.object(frappe, "db", MagicMock(exists=MagicMock(return_value="integration-1")), create=True),
			patch.object(resolver.frappe, "get_doc", return_value="doc", create=True),
		):
			doc, organization = resolver.get_organization_integration("LLM")
		self.assertEqual(doc, "doc")
		self.assertEqual(organization, "Acme")

	def test_multiple_memberships_fail_closed(self):
		with (
			patch.object(resolver, "is_platform_admin", return_value=False),
			patch.object(resolver, "organizations_for_user", return_value=["Acme", "Other"]),
		):
			with self.assertRaises(resolver.OrganizationIntegrationResolutionError):
				resolver.resolve_organization()

	def test_company_llm_does_not_fallback_to_platform_singleton(self):
		company_doc = SimpleNamespace(
			enabled=1,
			base_url="https://company.test/v1",
			default_model="company-model",
			api_key="company-secret",
			get_password=lambda _field: "company-secret",
		)
		with patch.object(
			omniroute.resolver,
			"get_organization_integration",
			return_value=(company_doc, "Acme"),
		):
			config = omniroute.load_config()
		self.assertEqual(config.base_url, "https://company.test/v1")
		self.assertEqual(config.api_key, "company-secret")

	def test_missing_company_llm_is_an_error(self):
		with patch.object(
			omniroute.resolver,
			"get_organization_integration",
			return_value=(None, "Acme"),
		):
			with self.assertRaises(omniroute.OmniRouteConfigError):
				omniroute.load_config()

	def test_company_bitrix_does_not_use_platform_webhook(self):
		company_doc = SimpleNamespace(
			get_password=lambda _field: "https://acme.example/rest/1/secret/",
		)
		with patch.object(
			bitrix_config.resolver,
			"get_organization_integration",
			return_value=(company_doc, "Acme"),
		):
			self.assertEqual(
				bitrix_config.resolve_bitrix_webhook_url(
					env={"BITRIX_REST_WEBHOOK_URL": "https://platform.example/rest/1/platform/"}
				),
				"https://acme.example/rest/1/secret/",
			)


if __name__ == "__main__":
	unittest.main()
