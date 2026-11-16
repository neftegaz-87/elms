"""Resolve Bitrix24 CRM webhook configuration for ELMS."""

from __future__ import annotations

import os
from typing import Any, Mapping

import frappe

from scripts.bitrix.rest_client import WebhookEndpoint

from elms.integrations import resolver

SETTINGS_DOCTYPE = "ELMS Integration Settings"
REST_ENV = "BITRIX_REST_WEBHOOK_URL"
BOARD_ENV = "BITRIX_WEBHOOK_URL"


def _settings_webhook_url() -> str | None:
	get_single = getattr(frappe, "get_single", None)
	if not callable(get_single):
		return None
	try:
		settings = get_single(SETTINGS_DOCTYPE)
	except Exception:
		return None
	if not int(getattr(settings, "bitrix_enabled", 0) or 0):
		return None
	url = ""
	get_password = getattr(settings, "get_password", None)
	if callable(get_password):
		try:
			url = str(get_password("bitrix_webhook_url") or "").strip()
		except Exception:
			url = ""
	if not url:
		url = str(getattr(settings, "bitrix_webhook_url", "") or "").strip()
	return url or None


def _organization_webhook_url(organization: str | None = None) -> tuple[str | None, str | None]:
	try:
		doc, resolved = resolver.get_organization_integration(
			"Bitrix24", organization=organization, allow_unscoped=True
		)
	except resolver.OrganizationIntegrationResolutionError as exc:
		raise ValueError(str(exc)) from exc
	if not resolved:
		return None, None
	if doc is None:
		raise ValueError("Bitrix24 integration is not configured for this organization")
	url = resolver.integration_secret(doc, "webhook_url")
	if not url:
		raise ValueError("Bitrix24 webhook is not configured for this organization")
	return url, resolved


def resolve_bitrix_webhook_url(
	env: Mapping[str, str] | None = None,
	*,
	organization: str | None = None,
) -> str:
	"""Return webhook URL from Desk settings or BITRIX_REST_WEBHOOK_URL.

	FORBIDDEN: silent use of board webhook env BITRIX_WEBHOOK_URL.
	"""
	environ = env if env is not None else os.environ
	company_url, resolved_organization = _organization_webhook_url(organization)
	if resolved_organization:
		return company_url or ""
	if BOARD_ENV in environ and not environ.get(REST_ENV) and not _settings_webhook_url():
		# Presence of board-only secret must not become a silent transport source.
		pass

	from_settings = _settings_webhook_url()
	if from_settings:
		return from_settings

	from_env = str(environ.get(REST_ENV) or "").strip()
	if from_env:
		return from_env

	raise ValueError(
		"Bitrix CRM webhook is not configured: set it in ELMS Integration Settings "
		f"or {REST_ENV}"
	)


def resolve_webhook_endpoint(
	env: Mapping[str, str] | None = None,
	*,
	organization: str | None = None,
) -> WebhookEndpoint:
	"""Build a validated WebhookEndpoint from Settings or REST env."""
	return WebhookEndpoint(url=resolve_bitrix_webhook_url(env=env, organization=organization))


def validate_bitrix_settings(enabled: Any, webhook_url: str | None) -> None:
	"""Fail-closed validation for Desk Bitrix CRM fields."""
	if not int(enabled or 0):
		return
	url = str(webhook_url or "").strip()
	if not url:
		frappe.throw(
			"Bitrix Incoming Webhook URL is required when Bitrix CRM is enabled",
			frappe.ValidationError,
		)
	try:
		WebhookEndpoint(url=url)
	except Exception as exc:
		frappe.throw(f"Bitrix Incoming Webhook URL is invalid: {exc}", frappe.ValidationError)
