from __future__ import annotations

from urllib.parse import urlparse

import frappe
from frappe.model.document import Document

from elms.elms_core.doctype.elms_integration_settings.elms_integration_settings import validate_integration_settings
from elms.integrations.bitrix_config import validate_bitrix_settings
from elms.tenant import is_company_admin, is_platform_admin, organizations_for_user


INTEGRATION_TYPES = {"LLM", "Bitrix24", "Custom API"}


def _current_user() -> str:
	return str(getattr(getattr(frappe, "session", None), "user", "Guest") or "Guest")


def _secret(doc: Document, fieldname: str) -> str:
	try:
		return str(doc.get_password(fieldname) or "").strip()
	except Exception:
		return str(getattr(doc, fieldname, "") or "").strip()


def _validate_custom_api(enabled: bool, base_url: str, webhook_url: str) -> None:
	if not enabled:
		return
	url = (base_url or webhook_url or "").strip()
	if not url:
		frappe.throw("Base URL или Webhook URL обязательны для Custom API", frappe.ValidationError)
	parsed = urlparse(url)
	if parsed.scheme not in ("http", "https") or not parsed.netloc:
		frappe.throw("URL интеграции должен быть http(s)-адресом", frappe.ValidationError)


class ELMSOrganizationIntegration(Document):
	def validate(self) -> None:
		if self.integration_type not in INTEGRATION_TYPES:
			frappe.throw("Недопустимый тип интеграции", frappe.ValidationError)
		if not frappe.db.exists("ELMS Organization", self.organization):
			frappe.throw("Организация интеграции не найдена", frappe.DoesNotExistError)

		current = _current_user()
		if is_company_admin(current) and not is_platform_admin(current):
			allowed = organizations_for_user(current)
			if self.organization not in allowed:
				frappe.throw("Нельзя изменить интеграцию другой организации", frappe.PermissionError)

		if self.integration_type == "LLM":
			validate_integration_settings(self.enabled, self.base_url, _secret(self, "api_key"))
		elif self.integration_type == "Bitrix24":
			validate_bitrix_settings(self.enabled, _secret(self, "webhook_url"))
		else:
			_validate_custom_api(self.enabled, self.base_url, _secret(self, "webhook_url"))

		duplicate = frappe.db.exists(
			"ELMS Organization Integration",
			{"organization": self.organization, "integration_type": self.integration_type},
		)
		if duplicate and duplicate != self.name:
			frappe.throw("Для этой организации такой тип интеграции уже существует", frappe.ValidationError)
