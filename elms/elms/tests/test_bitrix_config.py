"""Contracts for Bitrix CRM webhook resolution from Desk settings / env."""

from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import patch

import frappe

from elms.integrations import bitrix_config


class TestBitrixConfig(unittest.TestCase):
	def test_settings_url_wins_over_env(self):
		settings = SimpleNamespace(
			bitrix_enabled=1,
			bitrix_webhook_url="",
			get_password=lambda _field: "https://portal.example/rest/1/secretcode/",
		)
		env = {"BITRIX_REST_WEBHOOK_URL": "https://portal.example/rest/9/envtoken/"}
		with patch.object(frappe, "get_single", return_value=settings, create=True):
			endpoint = bitrix_config.resolve_webhook_endpoint(env=env)
		self.assertEqual(endpoint.url, "https://portal.example/rest/1/secretcode/")

	def test_env_rest_webhook_used_when_settings_disabled(self):
		settings = SimpleNamespace(bitrix_enabled=0, get_password=lambda _field: "https://portal.example/rest/1/secretcode/")
		env = {"BITRIX_REST_WEBHOOK_URL": "https://portal.example/rest/9/envtoken/"}
		with patch.object(frappe, "get_single", return_value=settings, create=True):
			endpoint = bitrix_config.resolve_webhook_endpoint(env=env)
		self.assertEqual(endpoint.url, "https://portal.example/rest/9/envtoken/")

	def test_board_webhook_env_is_not_accepted(self):
		env = {"BITRIX_WEBHOOK_URL": "https://board.example/rest/1/boardtoken/"}
		with patch.object(frappe, "get_single", side_effect=Exception("missing"), create=True):
			with self.assertRaises(ValueError):
				bitrix_config.resolve_bitrix_webhook_url(env=env)

	def test_validate_requires_url_when_bitrix_enabled(self):
		bitrix_config.validate_bitrix_settings(0, "")
		with self.assertRaises(frappe.ValidationError):
			bitrix_config.validate_bitrix_settings(1, "")
		with self.assertRaises(frappe.ValidationError):
			bitrix_config.validate_bitrix_settings(1, "https://portal.example/bad")
		bitrix_config.validate_bitrix_settings(1, "https://portal.example/rest/1/secretcode/")


if __name__ == "__main__":
	unittest.main()
