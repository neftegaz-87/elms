"""Contract tests for ELMS Integration Settings and knowledge assistant."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import frappe

if not hasattr(frappe, "throw"):
	def _throw(msg, exc=Exception, *args, **kwargs):
		raise exc(msg)
	frappe.throw = _throw

if not hasattr(frappe, "_"):
	frappe._ = lambda msg, *args, **kwargs: msg

if not hasattr(frappe, "whitelist"):
	def _whitelist(*_args, **_kwargs):
		def decorate(function):
			return function
		return decorate
	frappe.whitelist = _whitelist

if not hasattr(frappe, "session"):
	frappe.session = SimpleNamespace(user="Administrator")

if not hasattr(frappe, "ValidationError"):
	class _ValidationError(Exception):
		pass
	frappe.ValidationError = _ValidationError

if not hasattr(frappe, "PermissionError"):
	class _PermissionError(Exception):
		pass
	frappe.PermissionError = _PermissionError

if not hasattr(frappe, "AuthenticationError"):
	class _AuthenticationError(Exception):
		pass
	frappe.AuthenticationError = _AuthenticationError

from elms.ai import api as ai_api
from elms.ai import context as context_mod
from elms.ai import omniroute
from elms.elms_core.doctype.elms_integration_settings.elms_integration_settings import (
	validate_integration_settings,
)


ROOT = Path(__file__).resolve().parents[1]


class TestIntegrationSettingsSchema(unittest.TestCase):
	def setUp(self):
		self.path = (
			ROOT
			/ "elms_core"
			/ "doctype"
			/ "elms_integration_settings"
			/ "elms_integration_settings.json"
		)

	def test_integration_settings_single_exists_with_provider_fields(self):
		self.assertTrue(self.path.is_file())
		payload = json.loads(self.path.read_text(encoding="utf-8"))
		self.assertEqual(payload["name"], "ELMS Integration Settings")
		self.assertEqual(payload["issingle"], 1)
		self.assertEqual(payload["module"], "ELMS Core")
		fields = {item["fieldname"]: item for item in payload["fields"]}
		self.assertIn("enabled", fields)
		self.assertEqual(fields["enabled"]["fieldtype"], "Check")
		self.assertEqual(fields["omniroute_base_url"]["fieldtype"], "Data")
		self.assertEqual(fields["omniroute_api_key"]["fieldtype"], "Password")
		self.assertEqual(fields["default_model"]["fieldtype"], "Data")
		self.assertEqual(fields["omniroute_base_url"]["label"], "Base URL")
		self.assertEqual(fields["omniroute_api_key"]["label"], "API Key")
		roles = {item["role"] for item in payload["permissions"] if item.get("write")}
		self.assertIn("ELMS Admin", roles)
		self.assertIn("System Manager", roles)
		self.assertNotIn("ELMS Methodologist", roles)
		self.assertNotIn("ELMS Learner", roles)

	def test_validate_requires_url_and_key_when_enabled(self):
		validate_integration_settings(0, "", "")
		with self.assertRaises(frappe.ValidationError):
			validate_integration_settings(1, "", "secret")
		with self.assertRaises(frappe.ValidationError):
			validate_integration_settings(1, "http://host/v1", "")
		with self.assertRaises(frappe.ValidationError):
			validate_integration_settings(1, "ftp://host/v1", "secret")
		with self.assertRaises(frappe.ValidationError):
			validate_integration_settings(1, "http://host/api", "secret")
		validate_integration_settings(1, "http://host.docker.internal:20128/v1", "secret")


class TestOmniRouteClient(unittest.TestCase):
	def test_load_config_fail_closed_when_disabled(self):
		doc = SimpleNamespace(
			enabled=0,
			omniroute_base_url="http://example.test/v1",
			default_model="cx/gpt-5.6-luna-high",
			get_password=lambda *_a, **_k: "secret",
		)
		with patch.object(frappe, "get_single", return_value=doc, create=True):
			with self.assertRaises(omniroute.OmniRouteConfigError) as ctx:
				omniroute.load_config()
		self.assertEqual(ctx.exception.code, "config")
		self.assertTrue(ctx.exception.correlation_id)

	def test_list_models_and_complete_use_openai_compatible_paths(self):
		config = omniroute.ProviderConfig(
			enabled=True,
			base_url="http://provider.test/v1",
			api_key="k",
			default_model="cx/gpt-5.6-luna-high",
		)
		calls = []

		def fake_request(method, url, **kwargs):
			calls.append((method, url))
			if url.endswith("/models"):
				return {"data": [{"id": "cx/gpt-5.6-luna-high"}, {"id": "other"}]}
			return {"choices": [{"message": {"content": "answer from context"}}]}

		with patch.object(omniroute, "_request_json", side_effect=fake_request):
			models = omniroute.list_models(config)
			answer, cid = omniroute.complete(
				[{"role": "user", "content": "q"}],
				model="cx/gpt-5.6-luna-high",
				config=config,
			)
		self.assertEqual(models, ["cx/gpt-5.6-luna-high", "other"])
		self.assertEqual(answer, "answer from context")
		self.assertTrue(cid)
		self.assertEqual(calls[0], ("GET", "http://provider.test/v1/models"))
		self.assertEqual(calls[1], ("POST", "http://provider.test/v1/chat/completions"))


class TestContextAssembler(unittest.TestCase):
	def test_build_context_pack_includes_doctype_and_whitelist_sources(self):
		pack, sources = context_mod.build_context_pack(force=True)
		self.assertIn("ELMS Course", pack)
		self.assertIn("get_learning_relationships", pack)
		self.assertIn("elms.access.api.create_organization", pack)
		self.assertIn("platform grounded context", pack)
		self.assertIn("## Workspaces", pack)
		self.assertIn("/app/lms", pack)
		self.assertIn("/app/elms-learning", pack)
		resolved = context_mod.resolve_workspace({"pathname": "/app/lms", "route_str": "lms", "page": "lms"})
		self.assertIsNotNone(resolved)
		self.assertEqual(resolved["name"], "LMS")
		enriched = context_mod.enrich_view({"pathname": "/app/lms", "route": ["lms"], "page": "lms"})
		self.assertEqual(enriched["workspace"], "LMS")
		self.assertTrue(enriched.get("workspace_shortcuts"))
		self.assertTrue(enriched.get("workspace_links"))
		kinds = {item["kind"] for item in sources}
		self.assertIn("doctype", kinds)
		self.assertIn("method", kinds)
		refs = {item["ref"] for item in sources}
		self.assertTrue(any(ref.endswith("get_learning_relationships") for ref in refs))
		self.assertIn("elms.access.api.create_organization", refs)
		self.assertIn("elms.ai.api.get_access", refs)


class TestAIAssistantAPI(unittest.TestCase):
	def setUp(self):
		self._previous_session = getattr(frappe, "session", None)
		frappe.session = SimpleNamespace(user="methodologist@example.test")

	def tearDown(self):
		if self._previous_session is not None:
			frappe.session = self._previous_session
		else:
			frappe.session = SimpleNamespace(user="Administrator")

	def test_get_access_reflects_chat_roles(self):
		with patch.object(frappe, "get_roles", return_value=["ELMS Learner"], create=True):
			denied = ai_api.get_access()
		self.assertFalse(denied["allowed"])
		with patch.object(frappe, "get_roles", return_value=["ELMS Methodologist"], create=True):
			allowed = ai_api.get_access()
		self.assertTrue(allowed["allowed"])
		self.assertIn("ELMS Admin", allowed["roles"])

	def test_learner_cannot_call_get_models_or_ask(self):
		with patch.object(frappe, "get_roles", return_value=["ELMS Learner"], create=True):
			with self.assertRaises(frappe.PermissionError):
				ai_api.get_models()
			with self.assertRaises(frappe.PermissionError):
				ai_api.ask(question="Как найти связи?")

	def test_get_models_returns_allowlist_and_default(self):
		config = omniroute.ProviderConfig(
			enabled=True,
			base_url="http://provider.test/v1",
			api_key="k",
			default_model="cx/gpt-5.6-luna-high",
		)
		with (
			patch.object(frappe, "get_roles", return_value=["ELMS Methodologist"], create=True),
			patch.object(omniroute, "load_config", return_value=config),
			patch.object(omniroute, "list_models", return_value=["cx/gpt-5.6-luna-high", "other"]),
		):
			result = ai_api.get_models()
		self.assertEqual(result["default_model"], "cx/gpt-5.6-luna-high")
		self.assertEqual(result["models"], ["cx/gpt-5.6-luna-high", "other"])

	def test_ask_rejects_unknown_model_before_completions(self):
		config = omniroute.ProviderConfig(
			enabled=True,
			base_url="http://provider.test/v1",
			api_key="k",
			default_model="cx/gpt-5.6-luna-high",
		)
		with (
			patch.object(frappe, "get_roles", return_value=["ELMS Methodologist"], create=True),
			patch.object(omniroute, "load_config", return_value=config),
			patch.object(omniroute, "list_models", return_value=["cx/gpt-5.6-luna-high"]),
			patch.object(omniroute, "complete") as complete_mock,
		):
			with self.assertRaises(frappe.ValidationError):
				ai_api.ask(question="Как найти связи?", model="totally-unknown")
			complete_mock.assert_not_called()

	def test_ask_returns_answer_sources_and_correlation(self):
		config = omniroute.ProviderConfig(
			enabled=True,
			base_url="http://provider.test/v1",
			api_key="k",
			default_model="cx/gpt-5.6-luna-high",
		)
		with (
			patch.object(frappe, "get_roles", return_value=["ELMS Methodologist"], create=True),
			patch.object(omniroute, "load_config", return_value=config),
			patch.object(omniroute, "list_models", return_value=["cx/gpt-5.6-luna-high"]),
			patch.object(
				omniroute,
				"complete",
				return_value=(
					"Вызовите elms.lms.api.get_learning_relationships для поиска по связям.",
					"cid-1",
				),
			) as complete_mock,
			patch.object(
				context_mod,
				"build_context_pack",
				return_value=(
					"CONTEXT with elms.lms.api.get_learning_relationships and ELMS Course",
					[
						{"kind": "method", "ref": "elms.lms.api.get_learning_relationships"},
						{"kind": "doctype", "ref": "ELMS Course"},
					],
				),
			),
		):
			result = ai_api.ask(
				question="Что я вижу на этом окне?",
				view={
					"route": ["lms"],
					"route_str": "lms",
					"pathname": "/app/lms",
					"page": "lms",
					"headings": ["elms", "Кабинет обучения и плеер"],
				},
			)
		self.assertFalse(result["insufficient_data"])
		self.assertIn("get_learning_relationships", result["answer"])
		self.assertTrue(result["sources"])
		self.assertEqual(result["model"], "cx/gpt-5.6-luna-high")
		self.assertEqual(result["correlation_id"], "cid-1")
		self.assertEqual(result["view"]["workspace"], "LMS")
		self.assertTrue(result["view"].get("workspace_links"))
		self.assertTrue(result["view"].get("workspace_shortcuts"))
		source_refs = {item["ref"] for item in result["sources"]}
		self.assertNotIn("ELMS Integration Settings", source_refs)
		system = complete_mock.call_args.args[0][0]["content"]
		self.assertIn("CURRENT VIEW", system)
		self.assertIn("LMS", system)
		self.assertIn("workspace_shortcuts", system)
		self.assertIn("Кабинет обучения", system)

	def test_normalize_view_rejects_non_object(self):
		with self.assertRaises(frappe.ValidationError):
			ai_api._normalize_view([1, 2, 3])

	def test_ask_replaces_blind_claim_when_view_present(self):
		config = omniroute.ProviderConfig(
			enabled=True,
			base_url="http://provider.test/v1",
			api_key="k",
			default_model="cx/gpt-5.6-luna-high",
		)
		with (
			patch.object(frappe, "get_roles", return_value=["ELMS Admin"], create=True),
			patch.object(omniroute, "load_config", return_value=config),
			patch.object(omniroute, "list_models", return_value=["cx/gpt-5.6-luna-high"]),
			patch.object(
				omniroute,
				"complete",
				return_value=("Я не вижу содержимое текущего окна. Пришлите скриншот.", "cid-blind"),
			),
			patch.object(
				context_mod,
				"build_context_pack",
				return_value=("pack", [{"kind": "workspace", "ref": "LMS"}, {"kind": "doctype", "ref": "ELMS Course"}]),
			),
		):
			result = ai_api.ask(
				question="что я вижу?",
				view={"pathname": "/app/lms", "route": ["lms"], "page": "lms"},
			)
		self.assertFalse(result["insufficient_data"])
		self.assertIn("LMS", result["answer"])
		self.assertNotIn("скриншот", result["answer"].lower())
		self.assertEqual(result["view"]["workspace"], "LMS")

	def test_ask_fail_closed_when_disabled(self):
		with (
			patch.object(frappe, "get_roles", return_value=["ELMS Admin"], create=True),
			patch.object(
				omniroute,
				"load_config",
				side_effect=omniroute.OmniRouteConfigError("disabled", correlation_id="x"),
			),
		):
			with self.assertRaises(frappe.ValidationError) as ctx:
				ai_api.ask(question="q")
		self.assertIn("correlation_id=x", str(ctx.exception))

	def test_no_site_config_dual_path_in_ai_modules(self):
		for rel in ("ai/omniroute.py", "ai/api.py", "ai/context.py"):
			text = (ROOT / rel).read_text(encoding="utf-8")
			self.assertNotIn("frappe.conf", text)
			self.assertNotIn("get_site_config", text)
			self.assertNotIn("site_config", text)


class TestAssistantUIContract(unittest.TestCase):
	def test_desk_navbar_exposes_assistant_entry_and_api_wire(self):
		js = (ROOT / "public" / "js" / "desk-assistant.js").read_text(encoding="utf-8")
		css = (ROOT / "public" / "css" / "desk-assistant.css").read_text(encoding="utf-8")
		hooks = (ROOT / "hooks.py").read_text(encoding="utf-8")
		learning_js = (ROOT / "public" / "js" / "desk-learning.js").read_text(encoding="utf-8")
		self.assertIn("desk-assistant.js", hooks)
		self.assertIn("desk-assistant.css", hooks)
		self.assertIn("elms.ai.boot.extend_bootinfo", hooks)
		self.assertIn("elms_assistant_allowed", js)
		self.assertIn("header.navbar .search-bar", js)
		self.assertIn("data-elms-platform-assistant", js)
		self.assertIn("elms-navbar-assistant", js)
		self.assertIn("Помощник ELMS", js)
		self.assertIn("elms.ai.api.get_access", js)
		self.assertIn("elms.ai.api.get_models", js)
		self.assertIn("elms.ai.api.ask", js)
		self.assertIn("collectCurrentView", js)
		self.assertIn("pathnameWorkspaceSlug", js)
		self.assertIn("view:", js)
		self.assertIn("sessionStorage", js)
		self.assertNotIn("floating-fab", js.lower())
		self.assertNotIn("elms-assistant-fab", js)
		self.assertIn("elms-assistant-float", js)
		self.assertIn("data-elms-assistant-float", js)
		self.assertIn("assistant-close", js)
		self.assertIn("data-assistant-drag", js)
		self.assertIn("bindDrag", js)
		self.assertIn("elms-assistant-toolbar", js)
		self.assertIn("elms-assistant-send", js)
		self.assertNotIn("data-elms-platform-assistant", learning_js)
		self.assertNotIn("elms.ai.api.", learning_js)
		self.assertIn("elms-assistant-panel", css)
		self.assertIn("data-elms-assistant", css)
		self.assertIn(".elms-navbar-assistant", css)
		self.assertIn(".elms-assistant-float", css)
		self.assertIn("position: fixed", css)
		self.assertIn("cursor: grab", css)
		self.assertIn(".elms-assistant-toolbar", css)
		self.assertIn("text-overflow: ellipsis", css)
		self.assertIn("grid-template-columns: minmax(0, 1fr) 36px", css)
		self.assertIn(".elms-assistant-send", css)

	def test_settings_workspace_links_integration_settings(self):
		from elms.desk.workspaces import ELMS_WORKSPACE_DEFINITIONS

		settings = next(item for item in ELMS_WORKSPACE_DEFINITIONS if item["name"] == "Settings")
		link_to = [link[1] for link in settings["links"]]
		self.assertIn("ELMS Integration Settings", link_to)
		workspace_json = (
			ROOT / "elms_core" / "workspace" / "settings" / "settings.json"
		).read_text(encoding="utf-8")
		self.assertIn("ELMS Integration Settings", workspace_json)


if __name__ == "__main__":
	unittest.main()
