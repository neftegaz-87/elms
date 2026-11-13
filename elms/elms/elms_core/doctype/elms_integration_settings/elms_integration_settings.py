from urllib.parse import urlparse

import frappe

try:
	from frappe.model.document import Document
except ImportError:
	class Document:  # pragma: no cover - unit-test shim when Frappe package path is unavailable
		pass


def validate_integration_settings(enabled, base_url: str | None, api_key: str | None) -> None:
	if not enabled:
		return
	url = (base_url or "").strip()
	key = (api_key or "").strip()
	if not url:
		frappe.throw("Base URL is required when the knowledge assistant is enabled", frappe.ValidationError)
	parsed = urlparse(url)
	if parsed.scheme not in ("http", "https") or not parsed.netloc:
		frappe.throw("Base URL must be an http(s) URL", frappe.ValidationError)
	path = (parsed.path or "").rstrip("/")
	if not path.endswith("/v1"):
		frappe.throw("Base URL must end with /v1 (OpenAI-compatible API root)", frappe.ValidationError)
	if not key:
		frappe.throw("API Key is required when the knowledge assistant is enabled", frappe.ValidationError)


class ELMSIntegrationSettings(Document):
	def validate(self):
		api_key = None
		if self.enabled:
			try:
				api_key = self.get_password("omniroute_api_key")
			except Exception:
				api_key = getattr(self, "omniroute_api_key", None)
		validate_integration_settings(self.enabled, self.omniroute_base_url, api_key)
