# ELMS — оверлей над hub AGENTS.md

## Зачем (инструкция для агента)

Папка **`rules/`** — SoT настроек **этого** проекта для агентов (см. `rules/README.md`).

| Runtime | Как сюда попадает |
|---------|-------------------|
| Cursor | `.cursor/rules.d/` → symlink на `rules/*.mdc` |
| Codex | `AGENTS.override.md` в корне → Read `rules/` (override вместо hub `AGENTS.md`) |

`AGENTS.md` / `CLAUDE.md` — symlink на hub. Секции hub про ERPNext / CRM для **elms не применяются**.

**Открыт elms → продукт из `rules/`; workflow — hub AGENTS (Codex: после rules, путь из `.dev-hub`).**

## Продукт

Operations + LMS на Frappe Framework, app `elms`. Не CRM и не ERPNext.

## Lookup

| Тема | Источник |
|------|----------|
| Роли, DocPerm, атрибуты, LMS | `elms/elms/`, `memory-bank/product/modules.md` |
| Паттерны Frappe | `docs/vendor/framework/`, `frappe/`; CRM/ERP — только каркас |
| UI | neftegaz-ai-layer + LMS → `rules/elms-design.mdc` |

## Стиль кода и тестов (вместо hub «CRM»)

- Образец — соседний код в **`elms/`**, не `crm/`.
- API: `@frappe.whitelist()` + Document API; без параллельного FastAPI.
- Тесты: `FrappeTestCase` / bench `run-tests --app elms`.
- UI: scoped CSS app `elms`; не CRM Playwright runtime из hub AGENTS.

## Workflow

Ролевые команды (`BACK` / `FRONT` / `APP` / …) — как в hub `AGENTS.md`.  
Продукт и lookup — только `rules/` + `memory-bank/product/`.
