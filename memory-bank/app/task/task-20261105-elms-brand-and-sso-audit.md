---
execution: direct-ad-hoc
date: 2026-11-05
role: APP
mode: TASK
slug: elms-brand-and-sso-audit
---

# elms branding and SSO request audit

## Intent

Оставить на пользовательских поверхностях единый бренд `elms` вместо
`ELMS СДО` и смешанных `ELMS/LMS` заголовков. Проверить по локальным runtime
логам и данным сессии, были ли запросы для `erokhin.a@nftgz.ru` в Keycloak и
Yandex.

Внутренние имена DocType и RBAC-роли (`ELMS Admin`, `ELMS Operations User`,
`ELMS LMS User`) сохраняются: они участвуют в проверках прав и не являются
косметическим брендингом.

## Contract impact

Меняется только отображаемое имя приложения/учебной страницы/рабочих
пространств и соответствующие UI-контракты тестов. SSO-протокол не меняется.
Аудит runtime только читает Docker-логи и локальные Frappe/Keycloak БД.

## Files allowlist

- `memory-bank/app/task/task-20261105-elms-brand-and-sso-audit.md`
- `elms/elms/hooks.py`
- `elms/elms/install.py`
- `elms/elms/desk/workspaces.py`
- `elms/elms/public/js/desk-learning.js`
- `elms/elms/lms/workspace/lms/lms.json`
- `elms/elms/elms_core/workspace/settings/settings.json`
- `elms/elms/tests/test_login_ui.py`
- `elms/elms/tests/test_workspaces.py`
- `elms/elms/tests/test_learning_ui.py`

## Required lanes

- Targeted Python/UI contract tests for the changed branding surfaces.
- Frappe asset build for the changed Desk bundle.
- Read-only SSO audit: Keycloak container logs, Keycloak event/session tables,
  Frappe `tabUser`, `tabUser Social Login` and error log for the named account.

## Skipped lanes

- Browser/live HTTP smoke: not required for the read-only audit and no deploy
  is authorized in this task; asset build and targeted source contracts cover
  the small label-only UI change.
- Yandex/Keycloak writes: forbidden; no external state is changed.

## Selected skills

- None; no workflow skill is declared for this bounded task.

## Loop-safety preflight

`activeContext.md` is at the completed `T-A02` boundary and its `load_now`
contains only the completed decompose index. The allowlist does not overlap an
active implementation shard. Direct APP TASK must not modify `activeContext`,
roadmap, plan/decompose, implement artifacts, cursor files or loop indexes.

## Initial evidence

- Frappe `tabUser` records `last_login=2026-11-05 15:23:29.947875`,
  `last_ip=172.19.0.1` for `erokhin.a@nftgz.ru`.
- Frappe `tabUser Social Login` has provider rows `frappe` and `keycloak`,
  both modified at `2026-11-05 15:23:29.836550`.
- The successful login implementation calls Keycloak token and userinfo
  endpoints directly with `grant_type=password`; its browser path does not call
  the Yandex broker authorization endpoint.
- Keycloak event storage is empty and its container log contains no successful
  event for this user; therefore exact Keycloak request evidence is inferred
  from the successful Frappe Keycloak social-login record and application code,
  while Yandex absence is proven by the direct password-grant path plus no
  matching Keycloak/Yandex log record.

## Evidence

- Branding patch applied to the login context, app switcher, LMS workspace
  title/content, learning page header/tabs and workspace fixtures. Internal
  DocType and RBAC identifiers were not renamed.
- `python3 -m pytest -q elms/elms/tests/test_login_ui.py elms/elms/tests/test_workspaces.py elms/elms/tests/test_learning_ui.py`
  — 27 passed.
- `docker exec elms-dev-backend-1 bench build --app elms` — PASS; assets linked
  and production bundle built.
- Live asset check returns `<span>elms</span>` and `Управление обучением`, with
  no `ELMS СДО`/`Управление LMS` strings.
- `docker exec elms-dev-backend-1 bench --site elms.localhost migrate` — PASS;
  runtime LMS workspace title is `elms` and the login HTTP response contains
  `Вход на сайт elms`. Backend was restarted to load the updated hooks.
- For `erokhin.a@nftgz.ru`, Frappe records successful login at
  `2026-11-05 15:23:29.947875`, and `tabUser Social Login` has `keycloak` and
  `frappe` rows at `2026-11-05 15:23:29.836550`.
- Keycloak user `erokhin.a` exists and is enabled. Keycloak `event_entity` has
  zero rows, `user_session` has no durable row for this user, and the container
  log has no successful event or Yandex/broker line for this account. The only
  nearby Keycloak auth event is an unrelated `LOGIN_ERROR` for
  `elms.qa.invalid@example.test`.
- Frappe `tabError Log` has no entries for this account's login window around
  `15:23 MSK`.
- Conclusion: the login did call Keycloak's password-grant token endpoint and
  userinfo endpoint (the successful `provider=keycloak` Frappe record and the
  current login implementation establish this), but it did not call Yandex.
  The current browser submit path goes directly to Keycloak with
  `grant_type=password`; the Yandex broker is only used by the separate OIDC
  authorization URL path, which the current login JS does not invoke. Exact
  successful Keycloak HTTP lines cannot be recovered because access/success
  event persistence is not enabled in this dev stack.
