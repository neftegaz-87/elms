# Технический контекст

**Дата:** 2026-10-29  
**Обновлено:** 2026-11-14 (T-A09 APP QA PASS & context sync; T-A08 APP QA PASS & context sync); 2026-11-13 (T-A07 APP QA PASS & context sync); 2026-11-12 (observability: logs stay local / center reads); 2026-11-01 (observability stack decision); 2026-10-31 (T-B08 QA PASS & context sync; T-B07 QA PASS & context sync; T-B06 QA PASS & context sync; T-B05 QA PASS & context sync; T-A01 APP QA PASS; T-B04 QA PASS; T-B03 re-QA PASS & context sync)

## Стек

- **Frappe Framework v15** (vendor/framework tree в `frappe/`)
- Custom app **`elms`** (`elms/elms/`)
- MariaDB 11 + Redis (cache/queue)
- **Docker Compose SoT:** local — `docker/compose.dev.yaml`; production canonical — image-only `docker/compose.prod.yaml`, а local/CI build и staged/edge публикации вынесены в явные overlays.
- **Production boundary:** Vault/Vault Agent render gate, внутренние сети без host-портов, health/readiness, restart/security/resource policy и release image tag+digest проверяются до promotion. Production static secrets имеют единственный источник — KV v2 через authenticated Vault Agent render; local/env/dev fallback запрещён.
- Keycloak 24 (+ Postgres `keycloak-db`) в compose topology
- Desk UI (stock); Keycloak-only SSO через единый Social Login Key, без runtime IdP Yandex
- **Observability (хост ELMS):** логи остаются на машине ELMS (JSON stdout + ротация). Центр — отдельный sibling-репо `observability` (`~/PyProject/observability`): метрики/алерты с ops-машины, **чтение** логов по SSH/туннелю. Ship-to-central Loki / Vector remote sink — **FORBIDDEN**. Канон: [`decisions/observability-stack.md`](decisions/observability-stack.md).

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

## Фактическое дерево (as-built T-A09 + T-A07 + T-B08 + T-B07 + T-B06 + T-B05 + T-A01 + T-B04 + T-B03 re-QA)

```text
elms/                    # repo root
  .github/workflows/
    production-release.yml # gated immutable release and protected deploy handoff
  frappe/                # framework v15
  elms/                  # custom app
    pyproject.toml
    elms/
      hooks.py           # after_install, after_migrate, on_login, doc_events (User.after_insert)
      modules.txt        # ELMS Core, Operations, LMS
      install.py         # after_install / after_migrate setup (ensure_roles, ensure_section_perms, ensure_social_login_keys)
      elms_core/doctype/
        elms_settings_section/  # Single DocType (ELMS Core module RBAC anchor)
        elms_organization/      # B2B organization boundary
        elms_organization_member/ # Organization membership and User Permission scope
        elms_invite_log/         # Invite audit record
      access/
        api.py                   # Organization, Company Admin, invite and migration whitelist API
        keycloak.py              # Typed Keycloak Admin API client and provisioning errors
      cabinet/                   # Company Admin roster/progress and server-side export API
      operations/page/elms_cabinet/ # Desk Company Admin cabinet page
      elms_core/doctype/elms_cabinet_export_log/ # CSV export audit
      public/js/desk-cabinet.js  # roster/export UI wire
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
        test_sso.py             # Keycloak JIT, roles, fail-closed & fallback tests (22 tests)
        test_access_model.py    # Organization, membership and User Permission tests
        test_access_invite.py   # Invite, idempotency and provider-failure tests
  apps.json              # frappe + elms only
  docs/
    sso.md               # Keycloak-only SSO, JIT provisioning, migration & outage runbook
    bitrix-incoming-webhook.md  # Bitrix24 incoming webhook setup & env configuration manual
    operations/elms-production.md # backup/restore operator contract and production runbook
    reports/sso-browser-api-trace.json  # Typed live Frappe/Keycloak HTTP evidence
    reports/elms-production-qa-default-live-smoke.json # sanitized live HTTP smoke evidence
  docker/
    Dockerfile           # slim multi-stage build (vendor apps denied)
    compose.dev.yaml     # dev topology (backend, websocket, queues, scheduler, configurator, create-site, db, redis, keycloak, keycloak-db)
    compose.prod.yaml    # image-only production SoT
    compose.prod.build.yaml # explicit local/CI build overlay
    compose.prod.staged.yaml # isolated localhost/high-port rehearsal
    compose.prod.edge.yaml # explicit owner-approved edge overlay
    .env.dev.example
    .env.prod.example # non-secret production metadata and AppRole paths
    vault/              # pinned Raft config, Agent templates, policy and operator helpers
    caddy/Caddyfile.staged
    keycloak/realm-elms.json  # Realm elms and confidential client elms-frappe; no enabled Yandex IdP
    README.md            # Docker compose & SSO setup manual
  scripts/docker-up.sh
  scripts/live_smoke.sh  # Black-box Frappe/Keycloak HTTP smoke
    scripts/infra/        # Compose, Vault, secret, recovery and release contract checks
  ops/systemd/elms-backup.service # daily backup then verification caller
  ops/systemd/elms-backup.timer   # persistent daily backup schedule
  scripts/infra/backup_runner.py  # manifest, encrypted backup, freshness and disposable restore gates
  scripts/infra/check_release_manifest.py # immutable, non-secret release manifest validator
  scripts/infra/deploy_wrapper.py # allowlisted digest-pinned release/deploy/rollback gate
  scripts/infra/vault_snapshot.sh  # disposable synthetic/explicit-project Vault helper
  scripts/bitrix/
    __init__.py
    rest_client.py       # Bitrix24 REST webhook transport (post_json, WebhookEndpoint, CallArgs, RestEnvelope, token masking)
    call.py              # CLI for executing arbitrary Bitrix REST methods (exit codes 0/1/2)
    scope.py             # CLI for inspecting Bitrix webhook permissions and scopes (--full flag)
  tests/bitrix/
    __init__.py
    test_rest_client.py  # 37 unit tests for Bitrix REST client, CLI, guards, masking, docs
  tests/infra/           # production Compose/Vault/release/smoke contract tests
  .env.example           # BITRIX_REST_WEBHOOK_URL configuration template
  Makefile               # чистый (без legacy neftegaz)
  memory-bank/
    back/qa/T-B05-elms-production-container-stack/ # accepted typed QA evidence
    back/qa/T-B06-elms-vault-secrets/ # accepted typed QA evidence
    back/qa/T-B07-elms-backup-operations/ # accepted typed QA evidence
    back/qa/T-B08-elms-cicd-release-rollback/ # accepted typed QA evidence
    back/context-sync/T-B05-elms-production-container-stack/ # canonical sync report
    back/context-sync/T-B06-elms-vault-secrets/ # canonical sync report
    back/context-sync/T-B07-elms-backup-operations/ # canonical sync report
    back/context-sync/T-B08-elms-cicd-release-rollback/ # canonical sync report
    app/qa/T-A07-elms-b2b-org-keycloak-provisioning/ # accepted typed QA evidence
    app/context-sync/T-A07-elms-b2b-org-keycloak-provisioning/ # canonical sync report
    app/qa/T-A09-elms-company-admin-cabinet/ # accepted typed QA evidence
    app/context-sync/T-A09-elms-company-admin-cabinet/ # canonical sync report
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
6. SSO credentials: Frappe `site_config` содержит только `keycloak_login` (`client_id`, `client_secret`); Yandex client credentials не являются обязательными для SSO и runtime IdP Yandex удалён. Секреты в git tracking отсутствуют (fail-closed secret hygiene, TM-008).
7. Единая точка SSO в Frappe: ровно один Social Login Key (`Keycloak`) с провайдером `Keycloak` и каноническим redirect `/api/method/frappe.integrations.oauth2_logins.login_via_keycloak`; realm не содержит enabled Yandex provider или `kc_idp_hint` runtime dependency. Прямой Social Login Key Yandex или параллельные OAuth-модули в Frappe строго запрещены (SC-001, FR-010).
8. Идемпотентная конфигурация SSO: `ensure_social_login_keys` вызывается в `after_install` и `after_migrate`. Флаг `enable_social_login` управляется наличием учетных данных в `site_config` (conf gating, SC-002, TM-001).
9. Just-in-Time (JIT) провижининг сохраняется для первого входа через Keycloak: пользователь сопоставляется по неизменяемому `sub` и верифицированному email, без дубля; приглашённые пользователи дополнительно provisioned из ELMS в Keycloak через typed Admin API. Yandex-пользователи мигрируются на локальный Keycloak credential с обязательной сменой пароля, а migration aliases/data не образуют runtime IdP (SC-003, TM-004, TM-011).
10. Fail-closed назначение ролей: при регистрации нового пользователя хук `User.after_insert` (`maybe_assign_sso_roles`) гарантированно назначает роли `Desk User` и `ELMS LMS User`. Отсутствие любой из ролей вызывает исключение `frappe.throw` (fail-closed, запрещено создание учетной записи без прав, AC--3, TM-005).
11. Регламент сбоев и локальный fallback: сбой Keycloak блокирует вход без создания ложных сессий (fail-closed, BN-007, TM-009). Для авторизованных пользователей доступен локальный пароль Keycloak (`fallback.user@elms.local`, BN-008, TM-010), а для аварийного восстановления — локальный вход системного администратора в Frappe Desk (Break-Glass Level 2). Yandex broker happy-path не является runtime fallback.
12. Ролевая модель и секционные якоря: продуктовые роли включают `ELMS Admin`, `ELMS Operations User`, `ELMS Company Admin`, `ELMS Learner`, `ELMS Instructor`, `ELMS Methodologist`; секционные якоря — `ELMS Operations Section`, `ELMS LMS Section`, `ELMS Settings Section`. B2B-граница задаётся `ELMS Organization` и `User Permission`, а не User Group.
13. Fail-closed RBAC hooks: `ensure_roles` и `ensure_section_perms` вызываются при `after_install` и `after_migrate` (`elms/elms/install.py`).
14. Bitrix REST клиент и изоляция учетных данных: отдельная переменная окружения `BITRIX_REST_WEBHOOK_URL` формата `https://<domain>/rest/<user_id>/<webhook_code>/`. Тихий fallback на ключ доски (`BITRIX_WEBHOOK_URL`) строго запрещён (fail-closed exit code 2 без сетевого запроса).
15. Контракт кодов завершения Bitrix CLI (`call.py`, `scope.py`): 0 — успешный ответ Bitrix (JSON в stdout), 1 — ошибка Bitrix API (`error`, `error_description`) или сбой HTTP-транспорта (stderr, stdout пуст), 2 — ошибки валидации окружения, аргументов, неверный URL, некорректный JSON параметров или нарушение batch-ограничений (stderr, без сетевого вызова).
16. Защитные ограничения и маскирование секретов REST-клиента: маскирование секретного токена вебхука во всех сообщениях об ошибках, исключениях и строковых представлениях (`***`); валидация синтаксиса имени метода (`[a-z0-9_]+(\.[a-z0-9_]+)+`), обязательность JSON-объекта (dict) для `--params`; локальный batch guard (не более 50 команд, запрет вложенных batch).
17. Runtime SSO evidence gate: перед принятием live HTTP evidence `create-site` должен завершиться с кодом 0, а live/browser smoke — записать typed evidence со `status=pass`, `live_evidence=true` и `exit_code=0`; T-A07 подтвердил Keycloak discovery/login/authorization и B2B access/invite wire journey, а realm/runtime scan — отсутствие enabled Yandex provider и `kc_idp_hint`. Yandex остаётся migration-only compatibility inventory.
18. Login UI surface (`T-A01`): штатная страница Frappe `/login` остаётся единственным UI-владельцем входа; стандартная форма связывается с Keycloak через `login-keycloak.js`, рендерится ровно одна кнопка `.btn-keycloak` с публичным URL Keycloak (`KEYCLOAK_PUBLIC_URL/realms/elms`), прямой Yandex-контрол и template fork отсутствуют. `login.css` подключается через `web_include_css` и гарантирует стиль Neftegaz (специфичность и `!important` исключают переопределение со стороны `login.bundle.css`). Runtime browser evidence подтвердил `44px` высоту, `3px` radius и cobalt action `rgb(13, 76, 211)` (`#0d4cd3`). Все выявленные дефекты (BF-001..BF-004) закрыты.
19. Production boundary (`T-B05`): canonical `docker/compose.prod.yaml` — image-only SoT без `build`, source mounts и host-публикации внутренних сервисов; local/CI build, staged high-port rehearsal и owner-approved edge switch живут в отдельных overlays. Mandatory services проходят health/readiness, restart, `no-new-privileges` и bounded-resource checks; runtime/database secrets приходят через Vault Agent rendered files с fail-closed missing-key behavior; release manifest требует release tag плюс digest и отклоняет mutable/secret-like identity. Staged smoke использует изолированный project/high port и typed live evidence, а внешний review service остаётся отдельной signed-handoff boundary. Vault contract закрыт T-B06; backup/restore boundary закрыт T-B07; immutable CI release/deploy/rollback boundary закрыт T-B08; public edge cutover остаётся follow-up epic T-B09, а реальный Vault bootstrap/unseal и custody остаются operator gates.
20. Vault static-secret boundary (`T-B06`): production использует pinned integrated-Raft Vault на private Compose-only listener и authenticated AppRole/Vault Agent render. KV v2 policy `elms-agent` read-only и ограничена заявленными backend/Keycloak paths; MariaDB и Keycloak DB получают password files, Frappe/Keycloak/review/Yandex runtime получают rendered files. Sealed, unavailable, unauthorized или incomplete render блокирует promotion non-zero; root-token runtime, direct credential interpolation, public `8200`, local fallback и secret-value diagnostics запрещены. OAuth/session state остаётся writable application-owned state вне read-only Vault boundary.
21. Backup and disposable recovery boundary (`T-B07`): ELMS публикует полный non-secret state manifest для `sites`, logs, MariaDB, Keycloak PostgreSQL, Redis queue, Vault Raft и Caddy data/config; review-service application state остаётся во владении его repository и не дублируется. Backup выполняется client-side encrypted в off-host restic/S3-compatible repository, а promotion принимает только семантически verified evidence после backup и repository check с RPO 24h (возраст последнего успеха не более 24 часов). Недостаточная capacity блокирует upload/target creation до действия; автоматические prune/delete/volume removal запрещены. `restore-preflight` разрешает только явно отмеченный disposable target, отклоняет active volume/project, symlink и небезопасные/неотмеченные targets; redacted rehearsal contract покрывает RTO 4h для MariaDB, Keycloak PostgreSQL, Vault Raft и Caddy. External repository, credentials, custody, operations owner, target capacity и measured production RTO остаются operator gates.
22. Immutable CI release and pair rollback boundary (`T-B08`): contract/Compose/policy/secret, Frappe/app и browser gates завершаются до GHCR build/push; commit-SHA image refs и captured digests проходят non-secret manifest validation с Compose hash, smoke status и rollback verification. Protected production handoff требует GitHub Environment approval, explicit non-development target/root/wrapper и known-host-pinned SSH. Единственный state-changing wrapper под lock выполняет fixed digest-pinned Compose config/pull/up/health/internal-smoke sequence после semantic backup/Vault evidence; `current.json` записывается атомарно только после успеха. Forced health failure сохраняет predecessor, rollback применяет полный backend/frontend/application pair и не удаляет state volumes; status/evidence redacted. Реальный GHCR, SSH, protected approval и production deploy/rollback остаются operator gates.
23. Observability host-local logs (2026-11-12, supersedes 2026-11-01 ship-to-central): ELMS пишет JSON в stdout с ротацией; центр (`observability`) читает логи по запросу и держит только health/metrics/alerts. Loki/Grafana/Prometheus и remote log ship в ELMS compose запрещены. Детали: `memory-bank/decisions/observability-stack.md`. Эпик выравнивания: `T-B11-elms-host-local-logs-read-contract`.
24. B2B access and Keycloak provisioning (`T-A07`): `ELMS Organization` / membership / `ELMS Invite Log` задают организационную границу; `ELMS Company Admin` и Role Profile работают через User Permission scope. `create_organization`, `assign_company_admin`, `invite_org_user` и `migrate_yandex_users` — canonical whitelist methods. Invite success требует durable Frappe state, Keycloak Admin API provisioning и `UPDATE_PASSWORD`; provider failure is fail-closed, re-invite idempotent, password не возвращается. Realm/runtime — Keycloak-only, а live browser/API evidence подтвердил organization, denial, invite, password setup и login journey.
25. Company Admin cabinet (`T-A09`): `get_org_roster` и `export_org_progress` применяют server-side membership ACL; roster joins `ELMS Organization Member` → `ELMS Enrollment` → `ELMS Course Progress`, а missing progress документирован как `0.0`. Кабинет показывает empty state без fake rows. Export повторяет roster read model, генерирует UTF-8 CSV server-side и пишет `ELMS Cabinet Export Log`; DOM-only CSV запрещён. Authenticated runtime wire evidence прошёл roster/export journey и no-DOM-only-CSV check; active runtime использовал Keycloak-only credentials и preflight.

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
| Desk sections UI | `memory-bank/front/plan/T-F01-elms-desk-sections-roles/md/plan.md` | done (as-built T-F01, workspaces + role filter) |
| Bitrix REST client | `memory-bank/back/plan/T-B04-bitrix-rest-client/md/plan.md` | done (as-built T-B04, QA PASS) |
| Keycloak Login UI | `memory-bank/app/plan/T-A01-elms-keycloak-login-ui/md/plan.md` | done (as-built T-A01, QA PASS) |
| Production container stack | `memory-bank/back/plan/T-B05-elms-production-container-stack/md/plan.md` | done (as-built T-B05, QA PASS) |
| Vault secrets | `memory-bank/back/plan/T-B06-elms-vault-secrets/md/plan.md` | done (as-built T-B06, QA PASS) |
| Backup operations | `memory-bank/back/plan/T-B07-elms-backup-operations/md/plan.md` | done (as-built T-B07, QA PASS) |
| CI release and rollback | `memory-bank/back/plan/T-B08-elms-cicd-release-rollback/md/plan.md` | done (as-built T-B08, QA PASS) |
| Company Admin cabinet | `memory-bank/app/plan/T-A09-elms-company-admin-cabinet/md/plan.md` | done (as-built T-A09, QA PASS) |

## Тестовое покрытие (as-built T-A09 + T-A07 + T-B08 + T-B07 + T-B06 + T-B05 + T-A01 + T-B04 + T-B03 re-QA)

Исторический foundation-срез содержит 88 автоматических тестов: 51 в ELMS/Frappe suite и 37 в Bitrix suite; T-B06 QA дополнительно подтвердил полный прогон `87 passed, 2 skipped` и инфраструктурный прогон `27 passed`.
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
- T-A01 APP QA: `bin/pytest -q --tb=line` — 65 passed in 0.21s; `docker exec elms-dev-backend-1 bench build --app elms` — assets linked, done in 0.79s; `python3 scripts/run_browser_qa.py` и `bash scripts/live_smoke.sh` завершились с exit code 0.
- T-A01 runtime evidence: `browser-artifacts/browser-evidence.json` подтверждает live login page, один Keycloak control, отсутствие прямого Yandex-контрола и computed style; `docs/reports/sso-browser-api-trace.json` подтверждает journeys `JRN-SSO-001`, `JRN-SSO-001A`, `JRN-SSO-001B` и отсутствие прямого Frappe-вызова Yandex. Интерактивный Yandex остаётся `not_run`, broker endpoint без state вернул ожидаемый fail-closed `502`.
- T-B05 BACK QA: `bin/pytest -q --tb=line` — 87 passed, 2 skipped; `python3 -m pytest -q tests/infra` — 15 passed; staged dry-run, Compose/Vault/release policy checks и Bash syntax checks — PASS. Canonical live smoke без environment override записал `docs/reports/elms-production-qa-default-live-smoke.json` с `live_evidence=true`, `exit_code=0`, timestamp `2026-10-31T14:56:33Z`; BF-001 (T-B05 `behavior_smoke`) закрыт со статусом `done`, no-override regression подтверждён.
- T-B06 BACK QA: `bin/pytest -q --tb=line` — 87 passed, 2 skipped; `python3 -m pytest -q tests/infra` — 27 passed; Compose dev/prod config, Vault secret/policy contracts, preflight negative fixtures, recovery/redaction fixtures, Bash syntax и bounded legacy scans — PASS. Canonical live smoke записал `docs/reports/elms-production-qa-default-live-smoke.json` с `live_evidence=true`, `exit_code=0`, timestamp `2026-10-31T18:08:24Z`; BF-001/BF-002 закрыты, stale fallback tests/docs reconciled to fail-closed behavior.
- T-B07 BACK QA: `bin/pytest -q --tb=line` — 87 passed, 2 skipped; `bin/pytest tests/infra -q` — 43 passed; manifest/freshness/capacity/disposable-restore contracts, systemd ordering, redaction and bounded sunset/SOT scans — PASS. Sanitized canonical live smoke записал `docs/reports/elms-production-qa-default-live-smoke.json` с `live_evidence=true`, `exit_code=0`, timestamp `2026-10-31T19:56:42Z`; raw HTTP, cookies и tokens в QA evidence не копируются.
- T-B08 BACK QA: `bin/pytest -q --tb=line` — 87 passed, 2 skipped; `bin/pytest tests/infra -q` — 58 passed; immutable manifest/workflow ordering, protected target/wrapper, semantic backup/Vault evidence, forced-health-failure pair rollback, redaction and bounded sunset/SOT scans — PASS. Sanitized live HTTP smoke записал `docs/reports/elms-production-qa-default-live-smoke.json` с `live_evidence=true`, `exit_code=0`, timestamp `2026-10-31T19:56:42Z`; real GHCR, protected approval, SSH credentials и production deploy/rollback остаются operator gates.
- T-A07 APP QA: `./bin/pytest -q --tb=line` — 205 passed, 9 skipped, 5 subtests; targeted access/SSO behavior — 49 passed, 3 skipped; frontend syntax, migration, browser/live smoke and leftover-SOT scans — PASS. Live evidence подтвердило Keycloak discovery/login/authorization, `/app/elms-access`, organization/invite API, SMTP-captured `UPDATE_PASSWORD`, invited-user login и отсутствие runtime Yandex provider/`kc_idp_hint`; verify-qa PASS.
- T-A08 APP QA: app_lanes required lanes backend, frontend_build, browser, live_smoke, wire_journey и leftover_sot — PASS; AC-001..AC-005 — PASS. Public individual/legal forms create Bitrix Leads via `crm.lead.add` and persist `bitrix_id` fail-closed; `crm.lead.get.STATUS_ID` is the sole status SoT and ELMS keeps snapshot-only fields. Evidence is recorded in the QA YAML, typed browser evidence and live-smoke YAML; live Bitrix sandbox is out of scope and provider calls are mocked.
- T-A09 APP QA: required lanes backend, frontend_build, browser, live_smoke, wire_journey и leftover_sot — PASS; AC-001..AC-005 — PASS. Company Admin cabinet enforces server-side organization membership, joins members to enrollment/course progress, renders empty state, and exports server-side UTF-8 CSV with `ELMS Cabinet Export Log` audit. Authenticated runtime wire evidence passed roster/export and no-DOM-only-CSV checks; Keycloak-only active runtime credentials/preflight were required. Exploratory usability was not run as optional next action; blockers are empty.

## Государственные требования и сертификационные правила

В папке `memory-bank/compliance/` зафиксированы нормативные документы и требования регуляторов РФ, определяющие архитектуру данных, структуру DocTypes и правила валидации учебного контура:

1. **Реестр российского ПО (ПП РФ № 1236):** [`memory-bank/compliance/reestr-po-certification.md`](compliance/reestr-po-certification.md)
   - Автономность без зарубежных внешних облаков и сервисов; запрет скачивания зависимостей на старте (air-gapped режим).
   - Строгий запрет GPL/AGPL в прикладном коде; разрешены MIT, BSD, Apache 2.0. Обоснование LGPL для связки с СУБД.
   - Отсутствие внешних CDN и внешних шрифтов (локальные Source Sans 3, Onest, IBM Plex Mono, JetBrains Mono).
   - Полная русификация интерфейса и эксплуатационной документации; сборка на мощностях резидента РФ.
2. **ФИС ФРДО (Рособрнадзор):** [`memory-bank/compliance/fis-frdo-export.md`](compliance/fis-frdo-export.md)
   - Раздельные шаблоны выгрузок: модуль ДПО (40 колонок) и модуль ПО (35 колонок).
   - Формат файла: `ОГРН-КПП-год-номер.xlsx`, до 3000 строк на пакет, валидация СНИЛС по алгоритму СФР, код ОКСМ.
   - Подписание пакета УКЭП оператора (КриптоАРМ / ViPNet PKI Client).
   - Неизменяемые снимки документов (`snapshot`) при выдаче; дубликаты отдельными связанными записями.
   - Автоподача в ФИС ФРДО — **логика ОНАТО внутри ELMS** (порт; внешний ОНАТО не sole runtime) — [`architecture/integrations.md`](architecture/integrations.md).
2a. **Операционный контур ELMS:** единый учёт + ДО + заявки + автоподачи (Минтруд, ФРДО); устранение ручных стыков Прометей/Bitrix/Минтруд. Периметр: Bitrix24 · Прометей (миграция) · Минтруд · Олимпокс · ФИС ФРДО · ОНАТО как донор логики — [`architecture/integrations.md`](architecture/integrations.md).
3. **Охрана труда (ПП РФ № 2464):** [`memory-bank/compliance/ot-exam-attempts.md`](compliance/ot-exam-attempts.md)
   - Разграничение тренировочных тестов (самопроверка, без ограничений) и официальных проверок знаний (1 попытка на назначение, протокол комиссии).
   - 9 обязательных полей протокола (п. 92); состав комиссии не менее 3 человек.
   - Обязательное направление на пересдачу при оценке «неудовлетворительно» в течение не более 30 календарных дней (п. 79).
   - Запрет раскрытия слушателю правильных ответов для исключения компрометации банка вопросов.
4. **Миграция с СДО «Прометей»:** [`memory-bank/compliance/prometey-migration-checklist.md`](compliance/prometey-migration-checklist.md)
   - Замена действующей системы учебного центра без прерывания обучения («Прометей» отключается последним).
   - Сверка 7 контрольных количественных показателей (люди, организации, программы, зачисления, завершения, документы, протоколы).
   - СНИЛС как единственный ключ дедупликации физических лиц.
5. **152-ФЗ «О персональных данных»:** [`memory-bank/compliance/152-fz-privacy.md`](compliance/152-fz-privacy.md)
   - Хранение всех баз данных и файлов строго на территории РФ; запрет трансграничной передачи ПДн слушателей.
   - Разделение бессрочных реестров документов и ротируемой технической телеметрии.

## Открыто (после foundation)

- Доменные DocTypes Operations/LMS
- Нужен ли отдельный frontend SPA сверх Desk
