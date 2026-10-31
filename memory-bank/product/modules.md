# Модули ELMS

**Дата:** 2026-10-28  
**Обновлено:** 2026-10-30 (lookup: роли/атрибуты из LMS/`elms`; ERP/CRM только framework)

## Runtime

| Компонент | Роль |
|-----------|------|
| `frappe` | Framework v15 (единственная внешняя платформа) |
| `elms` | Наш custom app: Operations + LMS + Core |

## Модули app `elms` (`modules.txt`)

| Модуль | Назначение | Статус |
|--------|------------|--------|
| Core | Settings-секция, SSO ensure, общие install hooks | planned (T-B01+) |
| Operations | Бизнес-операции: BPM/workflows, документы, согласования, AI-автоматизация, задачи, интеграции (placeholder DocType секции) | planned (T-B02) |
| LMS | Учебный контур: курсы, программы, зачисления | foundation: RBAC-якорь; доменные сущности planned |

Классический ERP-контур (финансы, склад, закупки) **не** заявляется именем модуля или роли.

## Роли (продуктовые)

| Role | Desk разделы | Section DocTypes |
|------|--------------|------------------|
| `ELMS Admin` | Operations + LMS + Settings | все RWCD |
| `ELMS Operations User` | Operations | только `ELMS Operations Section` |
| `ELMS LMS User` | LMS | только `ELMS LMS Section` |

Дополнительно для входа в Desk: стандартная роль `Desk User` (назначается вместе с продуктовой).

### Матрица прав DocPerm (FR-004)

| Role | ELMS Operations Section | ELMS LMS Section | ELMS Settings Section |
| :--- | :--- | :--- | :--- |
| `ELMS Admin` | Read, Write, Create, Delete (RWCD) | Read, Write, Create, Delete (RWCD) | Read, Write, Create, Delete (RWCD) |
| `ELMS Operations User` | Read, Write (RW) | Deny (-) | Deny (-) |
| `ELMS LMS User` | Deny (-) | Read, Write (RW) | Deny (-) |
| `All` / `Guest` | Deny (-) | Deny (-) | Deny (-) |

Особенности авторизации:
- **Administrator**: системная учетная запись платформы Frappe, сохраняет полный доступ ко всем DocTypes в обход DocPerm (`Administrator not blocked`, FR-009).
- **System Manager**: системная роль Frappe для управления сайтом, не привязывается к продуктовым модулям ELMS автоматически.
- **Section DocTypes**: Single DocTypes (`ELMS Operations Section`, `ELMS LMS Section`, `ELMS Settings Section`), выступающие RBAC-якорями секций без бизнес-логики и доменных полей.
- **Fail-closed & no-skip**: доступ по умолчанию запрещен; права Guest отсутствуют; пропуски проверок запрещены (AC-6, AC--3).

## Placeholder DocTypes (RBAC якоря, без домена)

| DocType | Module |
|---------|--------|
| `ELMS Settings Section` | Core |
| `ELMS Operations Section` | Operations |
| `ELMS LMS Section` | LMS |

## LMS audit (as-built на 2026-10-30)

Источник истины для LMS — `elms/elms/lms/`. Сейчас в нём есть только:

- `ELMS LMS Section` — Single DocType в модуле `LMS`, технический RBAC-якорь;
- единственное поле `title` (`Data`, read-only, default `ELMS LMS Section`);
- `ELMS Admin`: полный доступ RWCD;
- `ELMS LMS User`: Read + Write, без Create/Delete.

Полноценных DocType `Course`, `Program`, `Enrollment`, `Learning Progress`, `Lesson`
и `Certificate` пока нет. Также нет LMS-specific Settings, API или UI для учебного
процесса. Поэтому пользователь с ролью `ELMS LMS User` получает базовый Desk-доступ
и права на якорь секции, но ещё не учебный кабинет с курсами.

`/app/setup-wizard/0` не является настройкой LMS: это системный мастер Frappe.
В `elms` нет `setup_wizard_stages`; язык, часовой пояс и прочие пункты этого экрана
не создают и не настраивают учебные сущности.

## SSO

| Провайдер | Механизм | Эпик |
|-----------|----------|------|
| Keycloak | Единственный Frappe Social Login Key `Keycloak` + контейнер в compose | T-B03 |
| Яндекс | OIDC Identity Provider/broker внутри Keycloak; не отдельный Frappe provider | T-B03 |

Default роль при SSO signup (dev): `ELMS LMS User` + `Desk User`.

## Workspaces (FRONT)

| Workspace | Roles |
|-----------|-------|
| Operations | ELMS Admin, ELMS Operations User |
| LMS | ELMS Admin, ELMS LMS User |
| Settings | ELMS Admin |

## Lookup при реализации

| Вопрос | Ответ в |
|--------|---------|
| Какие роли / DocPerm / секции | эта таблица + код `elms/elms/` (install, SSO roles, LMS) |
| Как устроен учебный домен | модуль **LMS** в `elms` (product SoT; сейчас только RBAC-якорь) |
| Как писать whitelist / DocType / hooks | `frappe/` + `docs/vendor/framework/`; ERP/CRM — только образец каркаса |
| Как выглядит UI | `memory-bank/product/design.md` (neftegaz + LMS) |

## DENY

| Что | Почему |
|-----|--------|
| ERPNext / Frappe LMS / Education / CRM / HRMS как apps | Пишем своё |
| Брать из ERP/CRM продуктовые роли, доменные поля или бренд | Канон — LMS/`elms`; ERP/CRM только framework-паттерны |
| Параллельный FastAPI/Django | Один runtime — Frappe |
| Копипаст DocType vendor wholesale | Только паттерны framework |
| Secrets SSO в git | Только env/site_config |
| Имя модуля/роли `ERP` | Канон T-B01: Operations заменяет ERP |
| Hub AGENTS секции CRM как SoT этого репо | Оверлей `rules/agents-overlay.md` |

## Правило

Новый модуль / DocType-группа / роль = запись сюда **до** кода.

**Стратегия выбора:** LMS-first для предметной области, ролей и настроек; ERP/CRM
система — вторичный read-only источник для зрелых паттернов Frappe (DocType,
permissions, workflow, list/form UI, hooks и API). В ELMS оставляем только то, что
лучше соответствует учебному сценарию; ERP/CRM-брендинг и чужая доменная модель в
пользовательский интерфейс не переносятся.
