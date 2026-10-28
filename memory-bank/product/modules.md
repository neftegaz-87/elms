# Модули ELMS

**Дата:** 2026-10-28  
**Обновлено:** 2026-10-28 (foundation plans)

## Runtime

| Компонент | Роль |
|-----------|------|
| `frappe` | Framework v15 (единственная внешняя платформа) |
| `elms` | Наш custom app: ERP + LMS + Core |

## Модули app `elms` (`modules.txt`)

| Модуль | Назначение | Статус |
|--------|------------|--------|
| Core | Settings-секция, SSO ensure, общие install hooks | planned (T-B01+) |
| ERP | Раздел ERP (пока placeholder DocType секции) | planned (T-B02) |
| LMS | Раздел LMS (пока placeholder DocType секции) | planned (T-B02) |

## Роли (продуктовые)

| Role | Desk разделы | Section DocTypes |
|------|--------------|------------------|
| `ELMS Admin` | ERP + LMS + Settings | все RWCD |
| `ELMS ERP User` | ERP | только `ELMS ERP Section` |
| `ELMS LMS User` | LMS | только `ELMS LMS Section` |

Дополнительно для входа в Desk: стандартная роль `Desk User` (назначается вместе с продуктовой).

## Placeholder DocTypes (RBAC якоря, без домена)

| DocType | Module |
|---------|--------|
| `ELMS Settings Section` | Core |
| `ELMS ERP Section` | ERP |
| `ELMS LMS Section` | LMS |

## SSO

| Провайдер | Механизм | Эпик |
|-----------|----------|------|
| Keycloak | Social Login Key `Keycloak` + контейнер в compose | T-B03 |
| Яндекс | Social Login Key `Custom` (`yandex`) | T-B03 |

Default роль при SSO signup (dev): `ELMS LMS User` + `Desk User`.

## Workspaces (FRONT)

| Workspace | Roles |
|-----------|-------|
| ERP | ELMS Admin, ELMS ERP User |
| LMS | ELMS Admin, ELMS LMS User |
| Settings | ELMS Admin |

## DENY

| Что | Почему |
|-----|--------|
| ERPNext / Frappe LMS / Education / CRM / HRMS как apps | Пишем своё |
| Параллельный FastAPI/Django | Один runtime — Frappe |
| Копипаст DocType vendor wholesale | Только паттерны |
| Secrets SSO в git | Только env/site_config |

## Правило

Новый модуль / DocType-группа / роль = запись сюда **до** кода.
