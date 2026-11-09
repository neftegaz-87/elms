---
execution: direct-ad-hoc
date: 2026-11-05
role: APP
mode: TASK
slug: dual-auth-login-password-and-yandex
---

# Dual login authentication: Yandex 360 SSO and Keycloak Login/Password

## Intent

Обеспечить поддержку двух полноценных способов входа на платформу ELMS:
1. Вход через корпоративный Yandex 360 (SSO брокер).
2. Вход по логину и паролю через защищённую форму Keycloak (для пользователей с локальными учетными записями, администраторов и внешних слушателей).

Вход по логину и паролю возвращается к прежней форме: ELMS передаёт введённые учетные данные внутреннему Keycloak и получает обратно сессию Frappe. Вход через Яндекс использует brokered Authorization Code flow и канонический callback Frappe.

## Contract impact

- В `elms/elms/sso/login.py` метод `get_sso_authorization_url` поддерживает режимы `yandex`, `password` (а также алиасы `keycloak` и `local`). Для режима `password`/`keycloak` запрос формируется без `kc_idp_hint`, открывая форму ввода логина/пароля в Keycloak с сохранением `login_hint`.
- В `elms/elms/public/js/login-keycloak.js` стандартная кнопка «Войти» отправляет логин/пароль в `login_with_keycloak`, а отдельная социальная кнопка показывает «Войти через Яндекс» и ведёт через Keycloak broker.
- В `elms/elms/public/css/login.css` добавлены стили Neftegaz для кнопки входа по паролю (`.elms-password-login`) и разделителя способов входа (`.elms-login-divider`).
- В тестах `elms/elms/tests/test_login_ui.py` и `elms/elms/tests/test_sso_mapping.py` добавлены проверки формирования URL и доступности обоих действий на клиенте.

## Files allowlist

- `memory-bank/app/task/task-20261105-dual-auth-login-password-and-yandex.md`
- `elms/elms/sso/login.py`
- `elms/elms/install.py`
- `elms/elms/public/js/login-keycloak.js`
- `elms/elms/public/css/login.css`
- `elms/elms/public/images/yandex.svg`
- `docker/keycloak/realm-elms.json`
- `elms/elms/tests/test_login_ui.py`
- `elms/elms/tests/test_sso_mapping.py`

## Required lanes

- Targeted Python tests for SSO URL generation, password bridge and login UI contract: PASS (35 passed).
- Frappe asset build for updated JS/CSS bundles: PASS (`bench build --app elms`).
- Live HTTP validation of the /login page, generated auth URLs and password login: PASS.

## Skipped lanes

- Interactive Yandex credentials login: dev container does not contain real external Yandex client secret.
- Production deployment.

## Selected skills

- None.

## Loop-safety preflight

`activeContext.md` remains untouched. Direct-ad-hoc APP TASK does not modify `activeContext.md`, roadmap, plan/decompose, implement artifacts, cursor or loop indexes.

## Evidence

- Unit & UI tests: `PYTHONPATH=elms python3 -m unittest elms.tests.test_login_ui elms.tests.test_keycloak_login elms.tests.test_sso_mapping elms.tests.test_sso_ensure` — 35 tests passed.
  - `test_login_js_submits_credentials_to_keycloak`: PASS.
  - Yandex broker URL and unsupported-mode checks: PASS.
- Full app tests: `PYTHONPATH=elms python3 -m unittest discover -s elms/elms/tests` — 127 passed, 2 skipped.
- Frappe asset bundle compiled and deployed via `bench build --app elms`.
- Live API response for `mode=password`:
  `auth_url` successfully generated without `kc_idp_hint`, directing user to Keycloak credential form with pre-filled `login_hint`.
- Live API response for `mode=yandex`:
  `auth_url` successfully generated with `kc_idp_hint=yandex`, directing user to Yandex 360 SSO broker.
- Live browser check: both fields and forgot-password link visible, no explanatory hint/test button, icons centered, Yandex icon rendered, password login reached `/app`.
