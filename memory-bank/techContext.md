# Технический контекст

**Дата:** 2026-10-28  
**Обновлено:** 2026-10-28 (T-B01 as-built)

## Стек

- **Frappe Framework v15** (vendor/framework tree в `frappe/`)
- Custom app **`elms`** (`elms/elms/`)
- MariaDB 11 + Redis (cache/queue)
- Docker Compose SoT для local: `docker/compose.dev.yaml` (compose.prod.yaml для prod)
- Keycloak 24 (+ Postgres `keycloak-db`) в compose topology
- Desk UI (stock); SSO через Social Login Key + Keycloak broker

## Фактическое дерево (as-built T-B01)

```text
elms/                    # repo root
  frappe/                # framework v15
  elms/                  # custom app
    pyproject.toml
    elms/
      hooks.py           # after_install, on_login hooks
      modules.txt        # Core, Operations, LMS
      install.py         # after_install setup & identity sync
      core/doctype/
      operations/doctype/
      lms/doctype/
  apps.json              # frappe + elms only
  docker/
    Dockerfile           # slim multi-stage build (vendor apps denied)
    compose.dev.yaml     # dev topology (backend, websocket, queues, scheduler, configurator, create-site, db, redis, keycloak, keycloak-db)
    compose.prod.yaml    # prod compose topology
    .env.dev.example
    keycloak/realm-elms.json
    README.md
  scripts/docker-up.sh
  Makefile               # чистый (без legacy neftegaz)
  memory-bank/
```

## Эталон паттернов (read-only)

`/home/aero/PyProject/PersonalProject/frappe-erp-crm`

- `docker/compose.dev.yaml`, `Dockerfile`, `scripts/docker-up.sh`
- `frappe/frappe/integrations/doctype/social_login_key`
- `frappe/frappe/integrations/oauth2_logins.py` (`login_via_keycloak`, `custom/<provider>`)

## Locked decisions (as-built)

1. Один custom app `elms` на одном Frappe site; `apps.json` и Dockerfile содержат строго `frappe` и `elms`.
2. Vendor apps (`erpnext`, `crm`, `hrms`, `education`) строго запрещены.
3. Fail-closed bootstrap: `create-site` выполняет `bench new-site` и `bench --site ... install-app elms`; ошибки не маскируются (`|| true` запрещён).
4. Docker = default local SoT. Топология включает `backend`, `websocket`, `queues`, `scheduler`, `configurator`, `create-site`, `db`, `redis`, `keycloak`, `keycloak-db`.
5. Keycloak service и `keycloak-db` развёрнуты в compose с realm seed `realm-elms.json`. Keycloak выступает центральным брокером идентичности; Frappe доверяет только Keycloak и управляет локальными ролями.
6. SSO credentials: `site_config` keys `keycloak_login`, `yandex_login`.
7. Ошибки явные; silent fallback FORBIDDEN.
8. App path: `elms/elms/hooks.py`; модули: `Core`, `Operations`, `LMS`.

## Board actors (Bitrix)

- Актёры и назначение эпиков: [`.loop/board-actors.yaml`](../.loop/board-actors.yaml)
  - `erokhin` = 274 (Андрей Ерохин) — default / «я»
  - `sokolov` = 240 (Евгений Соколов)
- Секреты доски и fallback `BITRIX_RESPONSIBLE_ID` — в `.env` (сейчас default 274).
- Ручной sync с актёром из yaml: `scripts/board-sync.sh <epic-id>` или `--all`.
- Авто `loop finish` пока берёт только `.env` `BITRIX_RESPONSIBLE_ID` (без per-epic yaml), пока не расширен hub.

## Планы foundation

| Ось | Plan | Статус |
|-----|------|--------|
| Docker bootstrap | `memory-bank/back/plan/T-B01-elms-docker-bootstrap/md/plan.md` | done (as-built T-B01) |
| Roles RBAC | `memory-bank/back/plan/T-B02-elms-roles-rbac/md/plan.md` | planned |
| SSO Keycloak+Yandex | `memory-bank/back/plan/T-B03-elms-sso-keycloak-yandex/md/plan.md` | planned |
| Desk sections UI | `memory-bank/front/plan/T-F01-elms-desk-sections-roles/md/plan.md` | planned |

## Открыто (после foundation)

- Доменные DocTypes Operations/LMS
- Нужен ли отдельный frontend SPA сверх Desk
