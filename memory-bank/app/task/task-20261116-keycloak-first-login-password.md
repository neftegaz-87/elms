---
execution: direct-ad-hoc
role: APP
mode: TASK
date: 2026-11-16
slug: keycloak-first-login-password
---

# Смена пароля при первом входе через интерфейс ELMS

## Intent

Приглашённый или созданный в Keycloak пользователь, для которого Keycloak
требует `UPDATE_PASSWORD` или который отмечен ELMS-маркером первого входа,
после входа должен увидеть обязательное модальное окно ELMS. Форма должна быть
частью штатной поверхности ELMS, а фактическая смена пароля и очистка маркера /
required action должны выполняться через Keycloak Admin API. После успешной
смены окно больше не показывается.

## Contract impact

- `GET elms.sso.password.get_password_change_state` возвращает `{required}` для
  текущей авторизованной Frappe-сессии.
- `POST elms.sso.password.change_password` принимает `new_password` и
  `confirm_password`, проверяет текущую сессию и актуальное состояние Keycloak,
  меняет пароль через Keycloak и удаляет только `UPDATE_PASSWORD` и
  `elms_first_login_password_change`.
- Desk UI запрашивает состояние и показывает блокирующее окно только при
  `required: true`.
- Публичный login flow и приглашение остаются Keycloak-boundary; пароль и
  required action не хранятся в Frappe.

## Explicit files allowlist

- `elms/elms/access/keycloak.py`
- `elms/elms/sso/password.py`
- `elms/elms/hooks.py`
- `elms/elms/public/css/first-login-password.css`
- `elms/elms/public/js/first-login-password.js`
- `elms/elms/tests/test_keycloak_admin.py`
- `elms/elms/tests/test_first_login_password.py`
- `elms/elms/tests/test_login_ui.py`
- `memory-bank/app/task/task-20261116-keycloak-first-login-password.md`

## Lanes

- backend: required — contract tests for Admin API and password boundary;
- frontend/build: required — static UI and hooks asset contract;
- wire: required — whitelist methods, Desk asset inclusion, and real Keycloak client
  calls are covered by tests; live HTTP/browser is not required for this task;
- browser/live_smoke: skipped — owner did not request deployment or live
  acceptance environment in this task.

## Selected skills

- none; product UI follows `rules/elms-design.mdc` and the existing ELMS
  scoped UI patterns.

## Loop-safety preflight

`memory-bank/activeContext.md` was read through its `load_now` path. The active
loop cursor is `T-A09-elms-company-admin-cabinet/DONE/DONE`; none of the files
in this task allowlist overlap its current shard, so this remains a direct
ad-hoc APP TASK and does not change loop state.

## Evidence

- Backend + wire: `PYTHONPATH=elms python3 -m unittest
  elms.tests.test_access_invite elms.tests.test_access_ui
  elms.tests.test_keycloak_admin elms.tests.test_first_login_password
  elms.tests.test_keycloak_login elms.tests.test_login_ui` — 43 tests passed.
- Frontend syntax: `node --check elms/elms/public/js/first-login-password.js` —
  passed.
- Python syntax: `python3 -m py_compile elms/elms/sso/password.py
  elms/elms/access/keycloak.py elms/elms/hooks.py` — passed.
- The custom modal is scoped to the ELMS Desk, uses the product cobalt/paper
  tokens, blocks the first-login surface until success, and does not load or
  render the Keycloak form.
- The invite provisioning path marks the Keycloak account with
  `elms_first_login_password_change`; completion removes that marker and only
  the `UPDATE_PASSWORD` action while preserving other Keycloak actions.
- Browser/live HTTP: skipped as declared; no deployment or external live state
  was changed.
