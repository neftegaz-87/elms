---
execution: direct-ad-hoc
date: 2026-11-05
role: APP
mode: TASK
slug: keycloak-yandex-broker-flow
---

# Keycloak → Yandex 360 brokered login

## Intent

Убрать direct password-grant из Frappe. Основной вход должен идти через
Authorization Code flow: Frappe направляет браузер в Keycloak, Keycloak
делегирует аутентификацию Yandex 360, затем возвращает код обратно в Frappe.
Для локальной разработки нужен отдельный тестовый режим локальной страницы
Keycloak; он не должен быть доступен в production.

## Contract impact

Пароль больше не передаётся из формы Frappe в серверный метод ELMS и не
передаётся Frappe в Keycloak. Основной маршрут получает только login hint и
возвращает browser redirect URL с `kc_idp_hint=yandex`. Локальный тестовый
режим разрешается только при `ELMS_ALLOW_LOCAL_KEYCLOAK_LOGIN=1`.

Проверка наличия корпоративной почты выполняется Yandex 360 в момент
аутентификации; доменная/организационная политика остаётся отдельным
конфигурируемым ограничением и не подменяется проверкой строки логина.

## Files allowlist

- `memory-bank/app/task/task-20261105-keycloak-yandex-broker-flow.md`
- `elms/elms/sso/login.py`
- `elms/elms/public/js/login-keycloak.js`
- `elms/elms/tests/test_sso_mapping.py`
- `elms/elms/tests/test_login_ui.py`
- `docker/keycloak/realm-elms.json`
- `docker/compose.dev.yaml`
- `docker/.env.dev`
- `docker/.env.dev.example`

## Required lanes

- Targeted SSO mapping and login UI tests.
- Keycloak realm JSON validation and live realm client configuration check.
- Frappe asset build and live login HTML/asset smoke.
- Local Keycloak authorization URL smoke for test accounts.

## Skipped lanes

- Interactive Yandex login: Yandex OAuth client credentials are empty in the
  current dev environment; no real Yandex account or external secret is
  available to the agent.
- Production deploy and production realm writes: not authorized.

## Selected skills

- None; no workflow skill is declared for this bounded task.

## Loop-safety preflight

`activeContext.md` is at the completed `T-A02` boundary and the current task
allowlist does not overlap an active implementation shard. Direct APP TASK must
not modify `activeContext`, roadmap, plan/decompose, implement artifacts,
cursor files or loop indexes.

## Evidence

Completed on the local dev stack (`elms-dev`):

- `elms/elms/sso/login.py` now returns an absolute callback URI. Live response:
  `http://elms.localhost:8082/api/method/frappe.integrations.oauth2_logins.login_via_keycloak`.
- `curl` authorization smoke returned `HTTP 303` from Keycloak and redirected to
  `/realms/elms/broker/yandex/login`; the previous `HTTP 400` caused by a
  hostless callback is resolved.
- Keycloak runtime contract verified: `elms-frappe` has
  `standardFlowEnabled=true`, `directAccessGrantsEnabled=false`, and the exact
  Frappe callback. The `yandex` broker is enabled with
  `first broker login` and `trustEmail=true`.
- Three dev verification users exist and are enabled:
  `elms.test.one@elms.local`, `elms.test.two@elms.local`,
  `elms.test.admin@elms.local`.
- Targeted Frappe tests: `elms.tests.test_sso_mapping` — 6 passed.
- Frappe asset build completed during backend restart; backend healthcheck is
  healthy.

The real Yandex interactive journey remains intentionally skipped because
`YANDEX_CLIENT_ID` and `YANDEX_CLIENT_SECRET` are empty in the local
environment. The Yandex OAuth application must be created and its secret
provided through local environment/Vault before that journey can complete.
