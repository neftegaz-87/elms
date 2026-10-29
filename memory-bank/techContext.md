# Технический контекст

**Дата:** 2026-10-29  
**Обновлено:** 2026-10-29 (T-B04 QA PASS; T-B03 re-QA PASS & context sync)

## Стек

- **Frappe Framework v15** (vendor/framework tree в `frappe/`)
- Custom app **`elms`** (`elms/elms/`)
- MariaDB 11 + Redis (cache/queue)
- Docker Compose SoT для local: `docker/compose.dev.yaml` (compose.prod.yaml для prod)
- Keycloak 24 (+ Postgres `keycloak-db`) в compose topology
- Desk UI (stock); SSO через единый Social Login Key + Keycloak broker (Yandex 360 OIDC IdP)

## Frappe documentation (offline SoT for API/how-to)

При вопросах по API/hooks/DocType/permissions/SSO Frappe **сначала** ходить в локальное зеркало, не угадывать из памяти:

| Path | Содержание |
|------|------------|
| `docs/vendor/framework/` | офлайн-зеркало https://docs.frappe.io/framework |
| `docs/vendor/framework/llms.txt` | индекс страниц |
| `docs/vendor/README.md` | как читать / как обновлять |

Физически symlink → `PersonalProject/frappe-erp-crm/docs/vendor/framework` (скачанный mirror). Обновление: `python3 docs/vendor/mirror-docs.py --spaces framework`. Справочник вендора ≠ продуктовый SoT ELMS (`memory-bank/` + `elms/`).

## Frappe documentation (offline SoT for API/how-to)

При вопросах по API/hooks/DocType/permissions/SSO Frappe **сначала** ходить в локальное зеркало, не угадывать из памяти:

| Path | Содержание |
|------|------------|
| `docs/vendor/framework/` | офлайн-зеркало https://docs.frappe.io/framework |
| `docs/vendor/framework/llms.txt` | индекс страниц |
| `docs/vendor/README.md` | как читать / как обновлять |

Физически symlink → `PersonalProject/frappe-erp-crm/docs/vendor/framework` (скачанный mirror). Обновление: `python3 docs/vendor/mirror-docs.py --spaces framework`. Справочник вендора ≠ продуктовый SoT ELMS (`memory-bank/` + `elms/`).

## Фактическое дерево (as-built T-B04 + T-B03 re-QA)

```text
elms/                    # repo root
  frappe/                # framework v15
  elms/                  # custom app
    pyproject.toml
    elms/
      hooks.py           # after_install, after_migrate, on_login, doc_events (User.after_insert)
      modules.txt        # ELMS Core, Operations, LMS
      install.py         # after_install / after_migrate setup (ensure_roles, ensure_section_perms, ensure_social_login_keys)
      elms_core/doctype/
        elms_settings_section/  # Single DocType (ELMS Core module RBAC anchor)
      operations/doctype/
        elms_operations_section/  # Single DocType (Operations module RBAC anchor)
      lms/doctype/
        elms_lms_section/       # Single DocType (LMS module RBAC anchor)
      sso/
        __init__.py
        constants.py     # Canonical SSO constants, endpoints, env vars, default roles
        conf.py          # Site config injection helper & role parser
        ensure.py        # Idempotent ensure_social_login_keys (Keycloak-only)
        roles.py         # JIT role assignment hook (User.after_insert: Desk User + ELMS LMS User)
      tests/
        test_roles_rbac.py      # RBAC / DocPerm unit tests (13 tests)
        test_sso_config.py      # SSO configuration, realm schema & secret hygiene tests (7 tests)
        test_sso_ensure.py      # Social Login Key ensure idempotency & gating tests (9 tests)
        test_sso.py             # Brokered JIT, roles, fail-closed & fallback tests (22 tests)
  apps.json              # frappe + elms only
  docs/
    sso.md               # SSO architecture, Yandex broker, JIT provisioning & outage runbook
    bitrix-incoming-webhook.md  # Bitrix24 incoming webhook setup & env configuration manual
    reports/sso-browser-api-trace.json  # Typed live Frappe/Keycloak HTTP evidence
  docker/
    Dockerfile           # slim multi-stage build (vendor apps denied)
    compose.dev.yaml     # dev topology (backend, websocket, queues, scheduler, configurator, create-site, db, redis, keycloak, keycloak-db)
    compose.prod.yaml    # prod compose topology
    .env.dev.example
    keycloak/realm-elms.json  # Realm elms, confidential client elms-frappe, yandex broker IdP
    README.md            # Docker compose & SSO setup manual
  scripts/docker-up.sh
  scripts/live_smoke.sh  # Black-box Frappe/Keycloak HTTP smoke
  scripts/bitrix/
    __init__.py
    rest_client.py       # Bitrix24 REST webhook transport (post_json, WebhookEndpoint, CallArgs, RestEnvelope, token masking)
    call.py              # CLI for executing arbitrary Bitrix REST methods (exit codes 0/1/2)
    scope.py             # CLI for inspecting Bitrix webhook permissions and scopes (--full flag)
  tests/bitrix/
    __init__.py
    test_rest_client.py  # 37 unit tests for Bitrix REST client, CLI, guards, masking, docs
  .env.example           # BITRIX_REST_WEBHOOK_URL configuration template
  Makefile               # чистый (без legacy neftegaz)
  memory-bank/
```

## Эталон паттернов (read-only)

`/home/aero/PyProject/PersonalProject/frappe-erp-crm`

- `docker/compose.dev.yaml`, `Dockerfile`, `scripts/docker-up.sh`
- `frappe/frappe/integrations/doctype/social_login_key`
- `frappe/frappe/integrations/oauth2_logins.py` (`login_via_keycloak`; direct `custom/<provider>` is not an ELMS SSO path)

## Locked decisions (as-built)

1. Один custom app `elms` на одном Frappe site; `apps.json` и Dockerfile содержат строго `frappe` и `elms`.
2. Vendor apps (`erpnext`, `crm`, `hrms`, `education`) строго запрещены.
3. Fail-closed bootstrap: `create-site` выполняет `bench new-site` и `bench --site ... install-app elms`; ошибки не маскируются (`|| true` запрещён).
4. Docker = default local SoT. Топология включает `backend`, `websocket`, `queues`, `scheduler`, `configurator`, `create-site`, `db`, `redis`, `keycloak`, `keycloak-db`.
5. Keycloak service и `keycloak-db` развёрнуты в compose с realm seed `realm-elms.json`. Keycloak выступает центральным брокером идентичности; Frappe доверяет только Keycloak и управляет локальными ролями.
6. SSO credentials: Frappe `site_config` содержит только `keycloak_login` (`client_id`, `client_secret`); Yandex client credentials передаются исключительно в контейнер Keycloak. Секреты в git tracking отсутствуют (fail-closed secret hygiene, TM-008).
7. Единая точка SSO в Frappe: ровно один Social Login Key (`Keycloak`) с провайдером `Keycloak` и каноническим redirect `/api/method/frappe.integrations.oauth2_logins.login_via_keycloak`. Прямой Social Login Key Yandex или параллельные OAuth-модули в Frappe строго запрещены (SC-001, FR-010).
8. Идемпотентная конфигурация SSO: `ensure_social_login_keys` вызывается в `after_install` и `after_migrate`. Флаг `enable_social_login` управляется наличием учетных данных в `site_config` (conf gating, SC-002, TM-001).
9. Just-in-Time (JIT) провижининг: пользователи создаются в Frappe строго just-in-time при первом входе через Keycloak брокер (`first broker login`), сопоставляются по неизменяемому `sub` и верифицированному email (SC-003, TM-004, TM-011). Массовый импорт каталога Yandex запрещён (FR-011).
10. Fail-closed назначение ролей: при регистрации нового пользователя хук `User.after_insert` (`maybe_assign_sso_roles`) гарантированно назначает роли `Desk User` и `ELMS LMS User`. Отсутствие любой из ролей вызывает исключение `frappe.throw` (fail-closed, запрещено создание учетной записи без прав, AC--3, TM-005).
11. Регламент сбоев и локальный fallback: авария внешнего IdP Yandex блокирует вход через брокер без создания ложных сессий (fail-closed, BN-007, TM-009). Для авторизованных пользователей доступен вход по локальному паролю Keycloak (`fallback.user@elms.local`, BN-008, TM-010). При отказе Keycloak доступен локальный вход системного администратора в Frappe Desk (Break-Glass Level 2).
12. Ролевая модель и секционные якоря: три продуктовые роли (`ELMS Admin`, `ELMS Operations User`, `ELMS LMS User`) и три Single DocTypes (`ELMS Operations Section`, `ELMS LMS Section`, `ELMS Settings Section`).
13. Fail-closed RBAC hooks: `ensure_roles` и `ensure_section_perms` вызываются при `after_install` и `after_migrate` (`elms/elms/install.py`).
14. Bitrix REST клиент и изоляция учетных данных: отдельная переменная окружения `BITRIX_REST_WEBHOOK_URL` формата `https://<domain>/rest/<user_id>/<webhook_code>/`. Тихий fallback на ключ доски (`BITRIX_WEBHOOK_URL`) строго запрещён (fail-closed exit code 2 без сетевого запроса).
15. Контракт кодов завершения Bitrix CLI (`call.py`, `scope.py`): 0 — успешный ответ Bitrix (JSON в stdout), 1 — ошибка Bitrix API (`error`, `error_description`) или сбой HTTP-транспорта (stderr, stdout пуст), 2 — ошибки валидации окружения, аргументов, неверный URL, некорректный JSON параметров или нарушение batch-ограничений (stderr, без сетевого вызова).
16. Защитные ограничения и маскирование секретов REST-клиента: маскирование секретного токена вебхука во всех сообщениях об ошибках, исключениях и строковых представлениях (`***`); валидация синтаксиса имени метода (`[a-z0-9_]+(\.[a-z0-9_]+)+`), обязательность JSON-объекта (dict) для `--params`; локальный batch guard (не более 50 команд, запрет вложенных batch).
17. Runtime SSO evidence gate: перед принятием live HTTP evidence `create-site` должен завершиться с кодом 0, а `scripts/live_smoke.sh` — записать `docs/reports/sso-browser-api-trace.json` со `status=pass`, `live_evidence=true` и `exit_code=0`; интерактивный Yandex остаётся `not_run` без реальных credentials и зарегистрированного callback.

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
| Roles RBAC | `memory-bank/back/plan/T-B02-elms-roles-rbac/md/plan.md` | done (as-built T-B02, QA PASS) |
| SSO Keycloak+Yandex | `memory-bank/back/plan/T-B03-elms-sso-keycloak-yandex/md/plan.md` | done (as-built T-B03, QA PASS) |
| Desk sections UI | `memory-bank/front/plan/T-F01-elms-desk-sections-roles/md/plan.md` | planned |
| Bitrix REST client | `memory-bank/back/plan/T-B04-bitrix-rest-client/md/plan.md` | done (as-built T-B04, QA PASS) |

## Тестовое покрытие (as-built T-B04 + T-B03 re-QA)

По текущему составу репозитория — 88 автоматических тестов: 51 в ELMS/Frappe suite и 37 в Bitrix suite; T-B03 re-QA подтвердил 51 passed.
- **Frappe / ELMS app suite:**
  - `bin/pytest -q --tb=line` — 51 passed in 0.11s
  - targeted SSO/RBAC regression: `bin/pytest -q --tb=line elms/elms/tests/test_sso.py elms/elms/tests/test_roles_rbac.py` — 39 passed
    - `test_roles_rbac.py` — 13 tests (роли, DocPerm матрица, fail-closed поведение)
    - `test_sso_config.py` — 7 tests (константы, клиент Keycloak, брокер Yandex, secrets hygiene)
    - `test_sso_ensure.py` — 9 tests (Social Login Key Keycloak-only, идемпотентность, conf-gating, отсутствие Yandex Social Login Key)
    - `test_sso.py` — 22 tests (JIT провижининг, fail-closed роли, outage branches, OAuth trace contract, runtime/bootstrap guards)
- **Bitrix REST suite:**
  - `python3 -m unittest discover tests/bitrix` — 37 tests in 0.007s
  - `bin/pytest tests/` — 37 passed in 0.10s
    - `test_rest_client.py` — 37 tests (валидация вебхука, изоляция от ключа доски, CLI call.py и scope.py, коды выхода 0/1/2, batch guard, маскирование секретов, документация docs/bitrix-incoming-webhook.md и .env.example)
- T-B03 runtime verification: `create-site` — `Exited (0)`; `bench --site elms.localhost list-apps` — `frappe 15.123.1`, `elms 0.0.1`; `scripts/live_smoke.sh` — exit 0 with typed HTTP evidence.

## Открыто (после foundation)

- Доменные DocTypes Operations/LMS
- Нужен ли отдельный frontend SPA сверх Desk
