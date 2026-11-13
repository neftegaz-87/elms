"""As-built context pack for the grounded knowledge assistant (no RAG)."""

from __future__ import annotations

import ast
import json
import re
import time
from pathlib import Path
from typing import Any

APP_ROOT = Path(__file__).resolve().parents[1]
CHAR_BUDGET = 120_000
CACHE_TTL_SEC = 60

_CACHE: dict[str, Any] = {"ts": 0.0, "pack": None, "sources": None, "workspaces": None}

REST_CHEAT_SHEET = """
ELMS REST patterns:
- Whitelist methods: POST /api/method/<dotted.path>
- DocType resource: /api/resource/<DocType>
- Platform assistant: elms.ai.api.get_access / get_models / ask
- Access / org: elms.access.api.*
- Learning: elms.lms.api.* (relationships, enroll, quiz flow)
- Integration settings Single: ELMS Integration Settings (только Workspace Settings / Form, НЕ Workspace LMS)
""".strip()

PAGE_SURFACES = """
Desk pages (route → what the screen is for):
- /app/elms-learning (page elms-learning): кабинет обучения. Tabs: Мои курсы, Каталог курсов, Программы, Учебный плеер, Прогресс и аттестация, Журнал активности, Управление обучением (manager).
- /app/elms-course-studio: конструктор курса (разделы/уроки/тесты: Practice|Assessment, Single/Multiple/True-False).
- /app/elms-course-preview: превью курса для методиста.
- Form/<DocType>: форма записи. List/<DocType>: список.
Navbar: Awesome Bar (#navbar-search) + Помощник ELMS (роль-gated).
""".strip()


def _scrub(value: str) -> str:
	text = re.sub(r"[^0-9a-zA-Zа-яА-ЯёЁ]+", "-", (value or "").strip().lower())
	return text.strip("-")


def _iter_workspace_json() -> list[dict[str, Any]]:
	results: list[dict[str, Any]] = []
	for path in sorted(APP_ROOT.glob("**/workspace/**/*.json")):
		if path.name.startswith("test_"):
			continue
		try:
			payload = json.loads(path.read_text(encoding="utf-8"))
		except (OSError, json.JSONDecodeError):
			continue
		if not isinstance(payload, dict):
			continue
		name = str(payload.get("name") or payload.get("label") or payload.get("title") or "").strip()
		if not name:
			continue
		if payload.get("doctype") not in (None, "Workspace") and "links" not in payload:
			continue
		links = []
		for item in payload.get("links") or []:
			if not isinstance(item, dict) or item.get("hidden"):
				continue
			entry = {
				"type": item.get("type"),
				"label": item.get("label"),
				"link_to": item.get("link_to"),
				"link_type": item.get("link_type"),
			}
			links.append(entry)
		shortcuts = []
		for item in payload.get("shortcuts") or []:
			if not isinstance(item, dict):
				continue
			shortcuts.append(
				{
					"label": item.get("label"),
					"type": item.get("type"),
					"url": item.get("url"),
					"link_to": item.get("link_to"),
				}
			)
		cards = []
		for item in links:
			if item.get("type") == "Card Break" and item.get("label"):
				cards.append(str(item["label"]))
		results.append(
			{
				"name": name,
				"label": payload.get("label") or name,
				"title": payload.get("title") or name,
				"module": payload.get("module"),
				"public": payload.get("public"),
				"slug": _scrub(str(payload.get("label") or name)),
				"links": links,
				"shortcuts": shortcuts,
				"cards": cards,
			}
		)
	return results


def get_workspaces(*, force: bool = False) -> list[dict[str, Any]]:
	if not force and _CACHE.get("workspaces") is not None:
		return list(_CACHE["workspaces"] or [])
	workspaces = _iter_workspace_json()
	_CACHE["workspaces"] = workspaces
	return list(workspaces)


def resolve_workspace(view: dict[str, Any]) -> dict[str, Any] | None:
	candidates: list[str] = []
	for key in ("workspace", "page", "route_str"):
		value = view.get(key)
		if isinstance(value, str) and value.strip():
			candidates.append(value.strip())
	route = view.get("route") or []
	if isinstance(route, list):
		for part in route:
			if part:
				candidates.append(str(part))
	path = ""
	for item in candidates:
		if "/app/" in item:
			path = item.split("/app/", 1)[-1].strip("/")
			if path:
				candidates.append(path.split("/", 1)[0])
	normalized = {_scrub(item) for item in candidates if item}
	if not normalized:
		return None
	for workspace in get_workspaces():
		names = {
			_scrub(workspace["name"]),
			_scrub(str(workspace.get("label") or "")),
			_scrub(str(workspace.get("title") or "")),
			_scrub(str(workspace.get("slug") or "")),
		}
		if normalized.intersection(names):
			return workspace
	return None


def enrich_view(view: dict[str, Any] | None) -> dict[str, Any]:
	data = dict(view or {})
	workspace = resolve_workspace(data)
	if not workspace:
		return data
	data["workspace"] = workspace["name"]
	data["workspace_module"] = workspace.get("module")
	data["workspace_cards"] = list(workspace.get("cards") or [])[:12]
	data["workspace_shortcuts"] = [
		{
			"label": item.get("label"),
			"url": item.get("url"),
			"link_to": item.get("link_to"),
			"type": item.get("type"),
		}
		for item in (workspace.get("shortcuts") or [])[:12]
	]
	data["workspace_links"] = [
		{
			"label": item.get("label"),
			"link_to": item.get("link_to"),
			"type": item.get("type"),
		}
		for item in (workspace.get("links") or [])
		if item.get("type") == "Link" and item.get("label")
	][:24]
	if not data.get("page"):
		data["page"] = f"workspace:{workspace['name']}"
	return data


def format_view_block(view: dict[str, Any] | None) -> str:
	if not view:
		return "CURRENT VIEW: (not provided by client)"
	lines = ["CURRENT VIEW:"]
	for key in (
		"route_str",
		"route",
		"page",
		"workspace",
		"workspace_module",
		"doctype",
		"docname",
		"title",
		"breadcrumbs",
		"headings",
		"labels",
		"active_tab",
		"workspace_cards",
		"workspace_shortcuts",
		"workspace_links",
	):
		value = view.get(key)
		if value in (None, "", [], {}):
			continue
		lines.append(f"- {key}: {value}")
	if len(lines) == 1:
		return "CURRENT VIEW: (empty)"
	return "\n".join(lines)


def explain_from_view(view: dict[str, Any] | None) -> str | None:
	data = dict(view or {})
	if not data:
		return None
	parts: list[str] = []
	workspace = str(data.get("workspace") or "").strip()
	doctype = str(data.get("doctype") or "").strip()
	page = str(data.get("page") or "").strip()
	route_str = str(data.get("route_str") or data.get("pathname") or "").strip()
	if workspace:
		parts.append(f"Открыт Workspace **{workspace}**" + (f" (`/{route_str.lstrip('/')}`)" if route_str else "") + ".")
		cards = data.get("workspace_cards") or []
		if cards:
			parts.append("Карточки: " + ", ".join(f"**{item}**" for item in cards) + ".")
		shortcuts = data.get("workspace_shortcuts") or []
		if shortcuts:
			bits = []
			for item in shortcuts:
				label = item.get("label")
				target = item.get("url") or item.get("link_to") or ""
				if label and target:
					bits.append(f"**{label}** → `{target}`")
				elif label:
					bits.append(f"**{label}**")
			if bits:
				parts.append("Быстрые переходы: " + "; ".join(bits) + ".")
		links = data.get("workspace_links") or []
		if links:
			bits = []
			for item in links[:12]:
				label = item.get("label")
				link_to = item.get("link_to")
				if label and link_to:
					bits.append(f"**{label}** → `{link_to}`")
				elif label:
					bits.append(f"**{label}**")
			if bits:
				parts.append("Ссылки: " + "; ".join(bits) + ".")
		return "\n".join(parts)
	if doctype:
		docname = str(data.get("docname") or "").strip()
		mode = "форма" if docname or "Form" in str(data.get("route") or []) else "список"
		line = f"Открыт {mode} DocType **{doctype}**"
		if docname:
			line += f" / `{docname}`"
		if route_str:
			line += f" (`{route_str}`)"
		parts.append(line + ".")
		labels = data.get("labels") or []
		if labels:
			parts.append("Поля/элементы на экране: " + ", ".join(str(item) for item in labels[:16]) + ".")
		return "\n".join(parts)
	if page:
		parts.append(f"Открыта страница **{page}**" + (f" (`{route_str}`)" if route_str else "") + ".")
		headings = data.get("headings") or []
		if headings:
			parts.append("Заголовки: " + ", ".join(f"**{item}**" for item in headings[:10]) + ".")
		labels = data.get("labels") or []
		if labels:
			parts.append("Элементы: " + ", ".join(str(item) for item in labels[:16]) + ".")
		return "\n".join(parts)
	if route_str or data.get("headings") or data.get("labels"):
		parts.append("Текущий маршрут: " + (route_str or "(без route)") + ".")
		if data.get("headings"):
			parts.append("Заголовки: " + ", ".join(str(item) for item in data["headings"][:10]) + ".")
		if data.get("labels"):
			parts.append("Элементы: " + ", ".join(str(item) for item in data["labels"][:16]) + ".")
		return "\n".join(parts)
	return None


def _workspace_pack_lines(workspaces: list[dict[str, Any]]) -> list[str]:
	lines = ["## Workspaces"]
	for workspace in workspaces:
		slug = workspace.get("slug") or _scrub(workspace["name"])
		shortcut_labels = [item.get("label") for item in workspace.get("shortcuts") or []]
		link_labels = [
			f"{item.get('label')}->{item.get('link_to')}"
			for item in workspace.get("links") or []
			if item.get("type") == "Link"
		]
		lines.append(
			f"- /app/{slug} (Workspace {workspace['name']}, module={workspace.get('module')}): "
			f"cards={workspace.get('cards')}; shortcuts={shortcut_labels}; links={link_labels}"
		)
	return lines


def _iter_doctype_json() -> list[tuple[str, dict[str, Any]]]:
	results: list[tuple[str, dict[str, Any]]] = []
	for path in sorted(APP_ROOT.glob("**/doctype/**/*.json")):
		if path.name.startswith("test_"):
			continue
		try:
			payload = json.loads(path.read_text(encoding="utf-8"))
		except (OSError, json.JSONDecodeError):
			continue
		if not isinstance(payload, dict):
			continue
		if payload.get("doctype") != "DocType" and "name" not in payload:
			continue
		name = payload.get("name") or path.stem
		if not str(name).startswith("ELMS"):
			continue
		fields = []
		for field in payload.get("fields") or []:
			if not isinstance(field, dict):
				continue
			if field.get("fieldtype") == "Password":
				continue
			fields.append(
				{
					"fieldname": field.get("fieldname"),
					"fieldtype": field.get("fieldtype"),
					"label": field.get("label"),
					"options": field.get("options"),
				}
			)
		results.append(
			(
				str(name),
				{
					"name": name,
					"module": payload.get("module"),
					"issingle": payload.get("issingle", 0),
					"fields": fields[:40],
				},
			)
		)
	return results


def _whitelist_signatures(module_path: Path, module_name: str) -> list[dict[str, str]]:
	if not module_path.is_file():
		return []
	try:
		tree = ast.parse(module_path.read_text(encoding="utf-8"))
	except (OSError, SyntaxError):
		return []
	out: list[dict[str, str]] = []
	for node in tree.body:
		if not isinstance(node, ast.FunctionDef):
			continue
		decorated = False
		for decorator in node.decorator_list:
			text = ast.dump(decorator)
			if "whitelist" in text:
				decorated = True
				break
		if not decorated:
			continue
		doc = ast.get_docstring(node) or ""
		args = [arg.arg for arg in node.args.args if arg.arg != "self"]
		out.append(
			{
				"ref": f"{module_name}.{node.name}",
				"signature": f"{node.name}({', '.join(args)})",
				"doc": doc.strip().splitlines()[0] if doc.strip() else "",
			}
		)
	return out


def build_context_pack(*, force: bool = False) -> tuple[str, list[dict[str, str]]]:
	now = time.time()
	if (
		not force
		and _CACHE["pack"] is not None
		and (now - float(_CACHE["ts"])) < CACHE_TTL_SEC
	):
		return _CACHE["pack"], list(_CACHE["sources"] or [])

	doctypes = _iter_doctype_json()
	workspaces = get_workspaces(force=force)
	methods: list[dict[str, str]] = []
	seen_methods: set[str] = set()
	for api_path in sorted(APP_ROOT.glob("**/api.py")):
		rel = api_path.relative_to(APP_ROOT)
		module_name = "elms." + ".".join(rel.with_suffix("").parts)
		for method in _whitelist_signatures(api_path, module_name):
			ref = method["ref"]
			if ref in seen_methods:
				continue
			seen_methods.add(ref)
			methods.append(method)

	sources: list[dict[str, str]] = []
	chunks: list[str] = [
		"# ELMS platform grounded context",
		"",
		"## REST cheat sheet",
		REST_CHEAT_SHEET,
		"",
		"## Desk pages",
		PAGE_SURFACES,
		"",
	]
	chunks.extend(_workspace_pack_lines(workspaces))
	chunks.append("")
	chunks.append("## Whitelist methods")
	sources.append({"kind": "surface", "ref": "desk-pages"})
	for workspace in workspaces:
		sources.append({"kind": "workspace", "ref": str(workspace["name"])})
	for method in methods:
		sources.append({"kind": "method", "ref": method["ref"]})
		chunks.append(f"- {method['ref']}: {method['signature']} — {method['doc']}")
	chunks.append("")
	chunks.append("## DocTypes")
	for name, payload in doctypes:
		sources.append({"kind": "doctype", "ref": name})
		field_names = ", ".join(
			str(f.get("fieldname")) for f in payload.get("fields") or [] if f.get("fieldname")
		)
		chunks.append(f"- {name} (module={payload.get('module')}; fields={field_names})")

	pack = "\n".join(chunks)
	if len(pack) > CHAR_BUDGET:
		pack = pack[: CHAR_BUDGET - 80] + "\n\n[context truncated to budget]\n"
	if not doctypes and not methods and not workspaces:
		raise ValueError("Grounded context pack is empty")

	_CACHE["ts"] = now
	_CACHE["pack"] = pack
	_CACHE["sources"] = sources
	_CACHE["workspaces"] = workspaces
	return pack, sources


def select_sources_for_answer(
	answer: str,
	sources: list[dict[str, str]],
	*,
	view: dict[str, Any] | None = None,
) -> list[dict[str, str]]:
	text = (answer or "").lower()
	picked: list[dict[str, str]] = []
	seen: set[str] = set()

	def add(source: dict[str, str]) -> None:
		ref = source.get("ref") or ""
		key = f"{source.get('kind')}:{ref}"
		if key in seen:
			return
		picked.append({"kind": source["kind"], "ref": ref})
		seen.add(key)

	view = view or {}
	workspace_name = str(view.get("workspace") or "").strip()
	if workspace_name:
		for source in sources:
			if source.get("kind") == "workspace" and source.get("ref") == workspace_name:
				add(source)
		for item in view.get("workspace_links") or []:
			link_to = str((item or {}).get("link_to") or "").strip()
			if not link_to:
				continue
			for source in sources:
				if source.get("kind") == "doctype" and source.get("ref") == link_to:
					add(source)

	for source in sources:
		ref = source.get("ref") or ""
		token = ref.lower()
		short = token.rsplit(".", 1)[-1]
		if token and (token in text or short in text):
			add(source)
		if len(picked) >= 12:
			return picked[:12]
	if picked:
		return picked[:12]

	fallback_doctypes = {"ELMS Course"}
	if workspace_name.lower() == "settings":
		fallback_doctypes.add("ELMS Integration Settings")
	for source in sources:
		ref = source.get("ref") or ""
		if source.get("kind") == "method" and "get_learning_relationships" in ref and workspace_name.upper() == "LMS":
			add(source)
		elif source.get("kind") == "doctype" and ref in fallback_doctypes:
			add(source)
		if len(picked) >= 4:
			break
	return picked[:12] or [{"kind": source["kind"], "ref": source["ref"]} for source in sources[:3]]
