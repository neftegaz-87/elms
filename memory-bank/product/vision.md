# ELMS — vision

**Path:** `memory-bank/product/vision.md`  
**Дата:** 2026-10-28  
**Обновлено:** 2026-10-30 (LMS-first lookup; ERP/CRM только framework-паттерны; дизайн neftegaz+LMS)  
**Проект:** `/home/aero/PyProject/elms`  
**Правила:** `rules/` (`elms-approach.mdc`, `elms-design.mdc`, `agents-overlay.md`) · Cursor symlink: `.cursor/rules.d/elms-*.mdc`

## Продуктовая идея

Своя система **Operations (бизнес-операции / BPM) + LMS** на **Frappe Framework**.  
Готовые apps (ERPNext, Frappe LMS, Education, CRM, HRMS) **не ставим и не форкаем как продукт**.

## Foundation (текущий горизонт)

Один Frappe site в Docker: app `elms`, MariaDB User/Administrator, три роли, Desk-разделы **Operations / LMS / Settings**, базовый SSO **Keycloak + Яндекс**.

Доменные сущности Operations/LMS — следующим горизонтом после foundation.  
Классический ERP (финансы, склад, закупки) в foundation **не** заявляется.

## Lookup (куда смотреть)

| Нужно | Источник |
|-------|----------|
| Роли, DocPerm, атрибуты пользователя, учебный домен | app **`elms`** (модуль LMS + Core/SSO), `memory-bank/product/modules.md` |
| Паттерны **фреймворка** Frappe | `docs/vendor/framework/`, `frappe/`; при необходимости read-only `/home/aero/PyProject/PersonalProject/frappe-erp-crm` **только каркас** (hooks/whitelist/DocType layout) |
| UI / visual language | `/home/aero/PyProject/neftegaz-ai-layer` + родной LMS UI → `memory-bank/product/design.md` |

**FORBIDDEN:** копать ERP/CRM за ролями, доменными атрибутами или UX продукта ELMS.

## Что берём из внешних эталонов

| Берём | Не берём |
|-------|----------|
| Frappe Framework (DocType, hooks, whitelist, desk, website) | ERPNext / CRM / Education / vendor LMS как установленные apps |
| Структуру app: `hooks.py`, `modules.txt`, `doctype/`, `api/`, `patches/` | Бизнес-логику и DocTypes CRM/ERP as-is |
| Дизайн neftegaz-ai-layer (токены, контролы) + LMS IA | CRM Desk chrome / brand imitation |
| Docker/compose, Social Login Key паттерны | Forge / Niche Audit / 1С-контур из frappe-erp-crm |

## HARD

1. SoT продукта — код в `/home/aero/PyProject/elms`, не vendor-apps.
2. Эталон `frappe-erp-crm` — read-only **только** framework-паттерны, не домен CRM.
3. Роли и атрибуты — из LMS/`elms`, не из CRM.
4. Новый модуль = явная запись в `memory-bank/product/modules.md` до реализации.
5. Секреты SSO не в git; ошибки без silent fallback.
6. Продуктовые модули/роли: `Core` / `Operations` / `LMS` — не `ERP`.
7. Hub `AGENTS.md` секции CRM — не канон; оверлей `AGENTS.elms.md`.
