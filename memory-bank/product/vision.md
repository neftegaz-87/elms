# ELMS — vision

**Path:** `memory-bank/product/vision.md`  
**Дата:** 2026-10-28  
**Обновлено:** 2026-11-16 (поступление: B2C оплата + B2B бланк/квоты; custom fields; 1С/Bitrix SoT вне текущего cut)  
**Проект:** `/home/aero/PyProject/elms`  
**Правила:** `rules/` (`elms-approach.mdc`, `elms-design.mdc`, `agents-overlay.md`) · Cursor symlink: `.cursor/rules.d/elms-*.mdc`

## Продуктовая идея

Своя система **Operations (бизнес-операции / BPM) + LMS** на **Frappe Framework**.  
Готовые apps (ERPNext, Frappe LMS, Education, CRM, HRMS) **не ставим и не форкаем как продукт**.

### Рыночная модель (канон)

ELMS — **открытая учебная платформа**: курсы проходят **любые люди**, которые хотят учиться (`ELMS Learner`), а не только сотрудники одной компании.

Компании — **партнёры платформы** (`ELMS Organization` + `ELMS Company Admin`):

1. подключаются к ELMS и **создают / публикуют свои курсы**;
2. и/или получают доступ к **курсам платформы** (каталог оператора ELMS) для своих потоков и договоров;
3. видят прогресс и отчёты по **слушателям своих курсов / потоков / договоров**, а не «список сотрудников в membership».

`ELMS Organization Member` — служебный контур **персонала партнёра** (админы, методисты, кураторы), а не модель «все ученики = сотрудники компании».  
Слушатель может не состоять в org партнёра: связь с партнёром идёт через **зачисление на курс/поток партнёра или платформы** (`ELMS Enrollment` → course/batch/subscription.organization).

Подробности ролей и сущностей: [`modules.md`](modules.md). Нормативные и B2B-практики: [`lms-best-practices.md`](lms-best-practices.md).

## Foundation (текущий горизонт)

Один Frappe site в Docker: app `elms`, MariaDB User/Administrator, три роли, Desk-разделы **Operations / LMS / Settings**, базовый SSO **Keycloak + Яндекс**.

Доменные сущности Operations/LMS — следующим горизонтом после foundation.  
Классический ERP (финансы, склад, закупки) в foundation **не** заявляется.

**ELMS** — единая система учёта, документооборота, заявок и автоподач (замена ручных стыков Прометей / Bitrix / Минтруд / ФРДО). Внешний периметр и перенос логики **ОНАТО** внутрь ELMS — [`architecture/integrations.md`](../architecture/integrations.md). SSO: Keycloak без Yandex.

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
