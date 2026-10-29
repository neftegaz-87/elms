# Модули ELMS

**Дата:** 2026-10-28  
**Обновлено:** 2026-10-29 (возврат канона T-B01: Operations вместо ERP)

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
| LMS | Учебный контур: курсы, программы, зачисления (placeholder DocType секции) | planned (T-B02) |

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

## DENY

| Что | Почему |
|-----|--------|
| ERPNext / Frappe LMS / Education / CRM / HRMS как apps | Пишем своё |
| Параллельный FastAPI/Django | Один runtime — Frappe |
| Копипаст DocType vendor wholesale | Только паттерны |
| Secrets SSO в git | Только env/site_config |
| Имя модуля/роли `ERP` | Канон T-B01: Operations заменяет ERP |

## Правило

Новый модуль / DocType-группа / роль = запись сюда **до** кода.
