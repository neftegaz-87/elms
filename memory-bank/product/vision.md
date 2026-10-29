# ELMS — vision

**Path:** `memory-bank/product/vision.md`  
**Дата:** 2026-10-28  
**Обновлено:** 2026-10-29 (Operations + LMS; ERP как имя модуля запрещён)  
**Проект:** `/home/aero/PyProject/elms`  
**Эталон кода:** `/home/aero/PyProject/PersonalProject/frappe-erp-crm` (только как пример)

## Продуктовая идея

Своя система **Operations (бизнес-операции / BPM) + LMS** на **Frappe Framework**.  
Готовые apps (ERPNext, Frappe LMS, Education, CRM, HRMS) **не ставим и не форкаем как продукт** — берём их только как **образец** организации кода, DocTypes, hooks, API, Desk/Website.

## Foundation (текущий горизонт)

Один Frappe site в Docker: app `elms`, MariaDB User/Administrator, три роли, Desk-разделы **Operations / LMS / Settings**, базовый SSO **Keycloak + Яндекс**.

Доменные сущности Operations/LMS — следующим горизонтом после foundation.  
Классический ERP (финансы, склад, закупки) в foundation **не** заявляется.

## Что берём из эталона

| Берём | Не берём |
|-------|----------|
| Frappe Framework (паттерны DocType, hooks, whitelist API, desk, website) | ERPNext / CRM / LMS / Education как установленные apps |
| Структуру app: `hooks.py`, `modules.txt`, `doctype/`, `api/`, `patches/` | Бизнес-логику и DocTypes чужих продуктов as-is |
| Docker/compose паттерны, Social Login Key | Forge / Niche Audit / 1С-контур из frappe-erp-crm |

## HARD

1. SoT продукта — код в `/home/aero/PyProject/elms`, не vendor-apps.
2. Эталон `frappe-erp-crm` — read-only справочник паттернов.
3. Новый модуль = явная запись в `memory-bank/product/modules.md` до реализации.
4. Секреты SSO не в git; ошибки без silent fallback.
5. Продуктовые модули/роли: `Core` / `Operations` / `LMS` — не `ERP`.
