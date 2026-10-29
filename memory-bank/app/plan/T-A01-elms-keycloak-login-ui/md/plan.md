# [T-A01 | elms-keycloak-login-ui] PLAN

**Дата:** 2026-10-29
**Режим:** APP PLAN
**Уровень:** L1
**Статус:** planned
**Prompt:** [md/prompt.md](prompt.md)
**Queue:** `memory-bank/app/roadmap/queue.yaml` → `T-A01` / `T-A01-elms-keycloak-login-ui`
**Batch:** `elms-auth-surface`
**Deps:** `T-B02-elms-roles-rbac`, `T-B03-elms-sso-keycloak-yandex`
**Related:** `T-F01-elms-desk-sections-roles` остаётся владельцем Workspaces; его login-affordance часть покрывается этим эпиком
**SUSPENSION GUARD:** active — plan output unlimited (§0.0)

---

## Решение

Делаем один рабочий вход на штатной странице Frappe `/login`. Frappe показывает единственную Social Login Key `Keycloak`, кнопка получает scoped-стиль в визуальном языке проекта `/home/aero/PyProject/neftegaz-ai-layer`, а OAuth-код продолжает обрабатываться стандартным Frappe callback. Keycloak показывает пользователю выбор Yandex 360; Yandex никогда не становится прямым Frappe-провайдером.

Весь runtime-конфиг и секреты приходят через `.env`/Docker Compose:

```text
Docker Compose env
  ├─ Frappe create-site/backend
  │    └─ site_config.keycloak_login + ELMS_SSO_* + public Keycloak URL
  └─ Keycloak import
       └─ elms realm + elms-frappe client + Yandex OIDC broker

GET /login
  └─ Social Login Key(Keycloak)
       └─ GET Keycloak /realms/elms/protocol/openid-connect/auth
            ├─ Yandex 360 broker
            └─ explicitly provisioned local Keycloak credential
                 └─ callback Frappe
                      └─ User by immutable sub + ELMS roles
                           └─ /app
```

`pydantic-settings` используется только на границе чтения окружения ELMS-owned Python config: typed settings валидируют env и формируют существующий `frappe.conf["keycloak_login"]`. Это не новый auth-stack и не второй источник runtime-правды; callback остаётся Frappe, а `frappe.conf` — его runtime SoT.

---

## Context consumed

| Path | Что вошло в решение |
|---|---|
| `memory-bank/activeContext.md` | текущий проект завершил BACK T-B03; следующий mixed slice может опираться на готовый Keycloak Social Login Key |
| `memory-bank/back/plan/T-B03-elms-sso-keycloak-yandex/md/plan.md` | Keycloak-only Frappe provider, Yandex broker, local fallback, default roles, callback и fail-closed правила |
| `elms/elms/sso/conf.py` | текущая injection boundary env → `site_config.json`; должна быть typed и сохраниться без прямого Yandex provider |
| `elms/elms/sso/ensure.py` | текущий idempotent Social Login Key `Keycloak`, public realm URL и отключение без credentials |
| `elms/elms/tests/test_sso.py` | текущие contract/behavior tests brokered и local identity linking, default roles и отсутствие Yandex Social Login Key |
| `elms/elms/tests/test_sso_config.py` | текущая проверка env → site config; сюда добавляется typed-settings contract |
| `frappe/frappe/www/login.html` | штатный anchor `.btn-login-option.btn-keycloak` и generated `provider.auth_url`; template fork запрещён |
| `frappe/frappe/www/login.py` | Social Login Key фильтрация, callback URL и отсутствие кнопки при невалидном provider config |
| `docker/compose.dev.yaml` | dev env → create-site/backend/keycloak, realm import и published URLs |
| `docker/compose.prod.yaml` | prod fail-fast secrets, HTTPS public URLs, Keycloak через Caddy |
| `docker/keycloak/realm-elms.json` | realm `elms`, client `elms-frappe`, Yandex OIDC broker, mappers и fallback user |
| `docker/.env.dev.example`, `docker/.env.prod.example` | public placeholders и secret variable contract |
| `scripts/live_smoke.sh` | live discovery, Frappe login, Keycloak authorization и broker endpoint checks |
| `/home/aero/PyProject/neftegaz-ai-layer/DESIGN.md` | approved light service UI, no gradients/brand imitation, compact controls, functional motion |
| `/home/aero/PyProject/neftegaz-ai-layer/frontend/src/index.css` | canonical rendered palette, typography scale, 4px spacing, 3px control radius, focus and reduced-motion rules |
| `/home/aero/PyProject/neftegaz-ai-layer/frontend/src/ui.jsx` | button geometry/state language: 44px control, cobalt primary, 1px border, subtle shadow, active/focus/disabled behavior |

---

## Product outcome (WHAT)

Сотрудник открывает ELMS, видит одну понятную кнопку `Login with Keycloak`/локализованный эквивалент и не должен знать внутренний `client_id`. Нажатие приводит на публичный Keycloak; там доступны Yandex 360 как brokered IdP и локальный пароль только для заранее provisioned Keycloak user. После успешного callback Frappe создаёт или находит локального User по `sub`, выдаёт согласованные роли и открывает Desk.

### Product decisions

| Вопрос | Решение |
|---|---|
| Где живёт login UI | штатный Frappe `/login`; без Vue/React SPA и без fork upstream template |
| Кто владеет auth contract | BACK T-B03 + этот APP slice как единый user journey; новый `/api/method` не создаётся |
| Где живёт Yandex | только Keycloak Identity Provider `alias=yandex`; Frappe не вызывает Yandex endpoints |
| Что происходит при отсутствии credentials | dev: Social Login Key выключен и кнопка отсутствует; prod/`ELMS_SSO_REQUIRE=1`: create-site завершается fail-fast |
| Как читаются env в Python | `pydantic-settings` typed adapter → существующий `inject_sso_site_config`; SecretStr не попадает в logs/repr |
| Как берётся дизайн | точные palette/geometry/state из Neftegaz source files, но CSS адаптируется к Frappe и scoped только к login surface |
| Как локализуется label | не переписывать DOM; provider остаётся `Keycloak`, стандартный Frappe translation допускает `Login with Keycloak` или русский эквивалент |

---

## Delivery closure

| Capability / outcome | Classification | Production entrypoint and caller | Success enforcement | Failure enforcement | Independent outcome test |
|---|---|---|---|---|---|
| Styled Keycloak login affordance | `vertical_slice` | Frappe `GET /login` → standard Social Login Key renderer → `.btn-keycloak` | exactly one enabled Keycloak provider renders an accessible link to public realm | no valid provider credentials → no SSO button; no hidden broken link | live `/login` contains exactly one Keycloak control, CSS asset and no direct Yandex control |
| Keycloak → Frappe login | `vertical_slice` | generated `provider.auth_url` → Keycloak authorize → `/api/method/frappe.integrations.oauth2_logins.login_via_keycloak` | code/state validation, token exchange, immutable `sub`, Frappe session and redirect to `/app` | denied auth, state mismatch, token error or missing identity produces no session and standard Frappe error | local Keycloak fallback user completes the real browser journey and lands in `/app` |
| Keycloak → Yandex broker | `vertical_slice` | Keycloak `/realms/elms/broker/yandex/endpoint` | configured Yandex client credentials are consumed by Keycloak; first broker login links realm identity | missing env or upstream error never creates a fake Frappe session; prod config fails closed | configured Yandex manual journey creates/links Keycloak identity and Frappe User |
| Env/Docker configuration | `vertical_slice` | Compose `.env` → create-site/backend/keycloak service environment | same client/URL/secret contract reaches the required service; prod validates HTTPS and required secrets | no secret in tracked realm/fixtures; missing required prod value stops startup | sanitized `docker compose config`/container env assertions plus no-secret scan |

Это не `foundation_only`: пользовательский результат — работающая кнопка и реальный auth journey, а не только CSS, resolver или realm JSON.

---

## User stories

| ID | Story | Priority | Independent Test |
|---|---|---:|---|
| US-001 | Как гость, я вижу одну визуально заметную кнопку входа через Keycloak на стандартной странице Frappe. | P0 | Given configured Keycloak; When GET `/login`; Then one `.btn-keycloak` is visible, keyboard-focusable and points to public Keycloak realm |
| US-002 | Как гость, я не вижу Yandex как отдельный Frappe provider. | P0 | Given configured broker; When GET `/login`; Then provider list has exactly Keycloak and no direct `yandex` Social Login Key/control |
| US-003 | Как сотрудник, я после клика прохожу настоящий Keycloak flow и возвращаюсь в Frappe Desk. | P0 | Given provisioned local Keycloak credential; When browser completes authorize/callback; Then authenticated session exists and `/app` opens |
| US-004 | Как сотрудник, я могу выбрать Yandex 360 на странице Keycloak. | P0 | Given non-empty `YANDEX_CLIENT_ID/SECRET`; When select Yandex in Keycloak; Then broker callback and Frappe callback finish with same user identity |
| US-005 | Как оператор dev, я могу настроить логин только через `.env`, не меняя JSON с секретом. | P0 | Given values in ignored env file; When Docker starts; Then create-site/backend/Keycloak use them and tracked files contain no real secret |
| US-006 | Как владелец prod, я получаю fail-closed результат при неполном SSO config. | P0 | Given `ELMS_SSO_REQUIRE=1` and missing Keycloak secret; When create-site runs; Then it exits non-zero before enabling a broken login button |
| US-007 | Как администратор, я могу использовать local Keycloak password только для выбранного realm user как fallback. | P1 | Given explicitly provisioned fallback credential; When Yandex is unavailable; Then same OIDC client creates the same Frappe session; no Yandex password is copied |
| US-008 | Как система, я сохраняю текущие Frappe RBAC/default-role invariants. | P0 | Given first broker/local login; When User is created; Then `Desk User` + configured ELMS role are assigned or signup is rejected; existing Frappe permissions remain authoritative |

---

## Functional requirements

### FR-001 — Standard Frappe login control

1. `GET /login` остаётся единственной публичной login page.
2. Frappe `login.py` должен найти ровно одну enabled Social Login Key с `provider_name=Keycloak`, valid `client_id`, public `base_url` и valid `keycloak_login` credentials.
3. Generated anchor сохраняет штатные Frappe attributes/href и получает существующий class path `.btn-login-option.btn-keycloak`; новый JS click handler не нужен.
4. Видимый текст должен содержать `Keycloak`; `client_id`, container hostname `keycloak:8080` и Yandex не могут быть единственным label.
5. При отсутствии credentials кнопка не рендерится в dev. При `ELMS_SSO_REQUIRE=1` конфигуратор/create-site не должен доводить site до состояния с битой кнопкой.

### FR-002 — Visual contract from Neftegaz

CSS создаётся в ELMS-owned asset `elms/elms/public/css/login.css`, публикуется как `/assets/elms/css/login.css` и подключается через `web_include_css` в `elms/elms/hooks.py`. Селекторы обязаны начинаться со login scope (`.for-login`/`.for-email-login` или equivalent page scope), чтобы не менять Desk и другие website controls.

| Token / behavior | Required value |
|---|---|
| Page paper | `#f5f7fa` |
| Surface | `#ffffff` |
| Graphite text | `#0b1f33` |
| Muted text | `#66727f` |
| Line | `#d5dce3` |
| Primary action | `#0d4cd3` |
| Primary border/hover | `#0a3fb0` |
| Soft action | `#eaf2ff` |
| Error / warning / success | `#b42318` / `#b54708` / `#167a4a` only for semantic states |
| Control height | `44px` minimum, matching Neftegaz `h-11` |
| Horizontal padding | `12px` minimum, no text clipping |
| Radius | `3px` for the button; no pill shape |
| Border | `1px solid` primary border |
| Shadow | subtle `0 1px 2px rgba(13, 76, 211, .28)`; no gradient |
| Text | 14px base, readable weight 500–600, inherit/local Frappe font stack |
| Focus | 2px action outline with 2px offset; visible without hover |
| Hover | darken to `#0a3fb0`, preserve contrast |
| Active | small `translateY(1px)` or brightness reduction, no layout shift |
| Disabled | pointer disabled and opacity about `.56`, never indistinguishable from absent |
| Motion | 120–160ms functional transitions; disable optional transition under `prefers-reduced-motion` |

The page/card may reuse paper/surface/line tokens only inside login scope. Do not copy Tailwind, React components, global `:root` tokens, remote fonts, logo, gradients or Neftegaz brand claims into Frappe.

### FR-003 — Frappe ↔ Keycloak contract

| Boundary | Contract |
|---|---|
| Browser | `GET /login` returns HTML; public control href is generated by Frappe OAuth helper |
| Authorization | `GET {KEYCLOAK_PUBLIC_URL}/realms/elms/protocol/openid-connect/auth` with `client_id=KEYCLOAK_CLIENT_ID`, redirect URI, state and OIDC scope |
| Yandex broker | Keycloak `GET/POST /realms/elms/broker/yandex/endpoint`; only Keycloak calls Yandex authorize/token/userinfo endpoints |
| Frappe callback | `GET /api/method/frappe.integrations.oauth2_logins.login_via_keycloak?code=<code>&state=<state>`; standard Frappe validates state/code and creates session |
| Success | HTTP redirect to `/app` or requested safe `redirect_to`; authenticated Frappe session and User link by `sub` |
| Failure | standard Frappe OAuth error/no session; configuration error is fail-fast in create-site when required |
| Authorization | initial `/login` is public; identity and Frappe roles are resolved after callback; Frappe DocPerm remains final authority |

No new Frappe whitelist method, FastAPI route, direct Yandex callback, raw OAuth client or custom session code is allowed.

### FR-004 — Environment and typed Python settings

1. `.env` is the only operator input. Committed files contain names, safe defaults and empty placeholders only.
2. `docker/compose.dev.yaml` passes the contract to `create-site`, `backend` and `keycloak`; `docker/compose.prod.yaml` passes required values with `${VAR:?VAR is required}` where secret/public HTTPS is mandatory.
3. `elms/elms/sso/settings.py` uses `pydantic-settings` and `SecretStr`; the existing `conf.py` delegates env parsing to this adapter for:
   - `KEYCLOAK_CLIENT_ID`
   - `KEYCLOAK_CLIENT_SECRET`
   - `KEYCLOAK_PUBLIC_URL`
   - `YANDEX_CLIENT_ID`
   - `YANDEX_CLIENT_SECRET`
   - `ELMS_SSO_DEFAULT_ROLES`
   - `ELMS_SSO_REQUIRE`
4. Typed settings must trim/validate URLs, parse boolean/role list, preserve an explicitly unconfigured Yandex state for local development, and never log secret values.
5. The adapter produces the existing `keycloak_login={client_id, client_secret}` site config only when both Keycloak credentials exist. It must remove legacy direct `yandex_login` if present.
6. Frappe runtime does not read Yandex credentials from site config. They are passed only to Keycloak.
7. Add `pydantic-settings` to `elms/pyproject.toml` only with a version compatible with the Frappe image/Python version; no ad-hoc dependency install in compose commands.

### FR-005 — Keycloak realm and Yandex broker

1. Realm remains `elms`; client remains confidential `elms-frappe` with standard authorization code flow.
2. Redirect URI uses `${FRAPPE_PUBLIC_URL}/api/method/frappe.integrations.oauth2_logins.login_via_keycloak`; local dev variants remain bounded to documented hosts/ports, not a broad production wildcard.
3. `KEYCLOAK_PUBLIC_URL` is the browser-visible issuer. `http://keycloak:8080` may be used only for container-internal connectivity and must never be emitted in the Frappe button href.
4. Identity provider is exactly `alias=yandex`, `providerId=oidc`, with `authorizationUrl=https://oauth.yandex.ru/authorize`, `tokenUrl=https://oauth.yandex.ru/token`, `userInfoUrl=https://login.yandex.ru/info`, trusted email and first-broker-login flow.
5. Yandex credentials are `${env.YANDEX_CLIENT_ID:}` and `${env.YANDEX_CLIENT_SECRET:}` in realm import/configuration. `docker/keycloak/entrypoint.sh` copies the read-only realm template to the writable import directory and makes the enabled state explicit: both values empty → broker disabled in dev; exactly one value → bootstrap fails; both values present → broker enabled. No fake enabled provider with empty credentials.
6. Mappers normalize `default_email`, `first_name`, and `last_name` into Keycloak claims consumed by Frappe.
7. `registrationAllowed=false` remains compatible with first-broker-login provisioning; public Keycloak registration is not enabled.
8. Local username/password remains enabled only for explicitly provisioned realm users. No Yandex password is copied into Keycloak or Frappe.
9. Dev and prod Compose services invoke the same entrypoint and mount the realm template read-only outside the generated import directory; the entrypoint is the only component allowed to prepare the import copy.

### FR-006 — Existing Frappe backend behavior remains the only SoT

1. Reuse T-B03 `ensure_social_login_keys()` and current `after_install/after_migrate` wiring; update only gaps needed for the UI/env contract.
2. Keep exactly one Social Login Key named/scrubbed `keycloak`; a negative test must assert no direct `yandex` row or provider constant.
3. Keep `user_id_property=sub` and one-way Keycloak→Frappe identity/profile/status/group reconciliation.
4. Keep default role behavior: new SSO user receives configured `Desk User` + `ELMS LMS User` in dev, or signup fails closed if a required role is missing.
5. `sign_ups=Deny` remains an explicit Frappe site setting for prod-like deployments; no UI control may claim success for a denied new user.

### FR-007 — Documentation/operator path

Update `docker/README.md` with a single reproducible path:

1. copy `docker/.env.dev.example` to ignored `docker/.env.dev`;
2. set Keycloak client secret and Yandex OAuth client ID/secret;
3. register the Yandex redirect URI as `https://<auth-host>/realms/elms/broker/yandex/endpoint` (or documented dev URL);
4. start Compose and wait for create-site/realm import;
5. open `/login`, click the only Keycloak button, choose Yandex on Keycloak, complete first-broker-login;
6. inspect linked Keycloak identity and Frappe User/roles;
7. test the documented local fallback user while Yandex is unavailable;
8. use clear-cache/migrate instructions when changing Social Login Key or CSS asset.

The README must state where each secret is consumed and must not print real values.

### FR-008 — Independent verification

Required evidence covers behavior, not only file presence:

- Frappe tests assert generated provider config, settings branches, role branches and no direct Yandex provider.
- Login HTML test asserts exactly one Keycloak anchor, its generated public href and CSS asset inclusion when enabled; disabled branch asserts no anchor.
- Live smoke asserts Keycloak discovery, Frappe login page, authorization redirect, broker endpoint and absence of container-only issuer in browser-visible URL.
- Docker config test asserts all required services receive the intended variable names and prod missing-secret path exits non-zero.
- Static bounded scan asserts no non-example secret and no direct Frappe Yandex OAuth route.
- Browser/manual evidence covers the actual click journey and visual states; backend-only green is insufficient for APP QA.

---

## UI element and state registry

| Element ID | Surface / selector | States | Owner / assertion |
|---|---|---|---|
| `UI-LOGIN-PAGE` | Frappe `/login`, `.for-login` | default, SSO disabled, error return | standard Frappe template remains intact |
| `UI-SSO-GROUP` | `.social-logins .social-login-buttons` | one provider, empty provider list | no second Yandex button; no empty decorative block |
| `UI-KEYCLOAK-BUTTON` | `.for-login a.btn-login-option.btn-keycloak` | default, hover, focus-visible, active, disabled/aria-disabled if emitted | text contains Keycloak; href is generated public Keycloak URL; 44px/3px/cobalt contract |
| `UI-KEYCLOAK-PAGE` | Keycloak realm `elms` | Yandex choice, local credential, upstream error | choices are Keycloak concerns, not Frappe controls |
| `UI-AUTH-CALLBACK` | Frappe callback path | success, denial, state/token error, missing email/role | session is created only on valid callback |
| `UI-DESK-REDIRECT` | `/app` | authenticated, forbidden/guest redirect | T-B02/T-F01 roles and workspace permissions remain authoritative |

---

## Acceptance scenarios

### AC-001 — Configured login button

Given `KEYCLOAK_CLIENT_ID`, `KEYCLOAK_CLIENT_SECRET`, `KEYCLOAK_PUBLIC_URL` and `ELMS_SSO_REQUIRE=1` are valid, when the site is migrated and `GET /login` is requested, then:

- the page contains exactly one visible `.btn-keycloak` control;
- the control is accessible by keyboard and has visible focus styling;
- its href starts with the public `KEYCLOAK_PUBLIC_URL/realms/elms`, never `keycloak:8080`;
- the label contains `Keycloak`;
- the page contains no direct Yandex provider/control;
- the ELMS login CSS asset is loaded.

### AC-002 — Styled visual states

Given the configured button, when a user hovers, focuses, activates and temporarily disables it, then it uses the Neftegaz palette/geometry, maintains readable contrast, does not shift layout, and the reduced-motion media rule removes optional transitions. The CSS does not alter an unrelated Frappe/Desk button.

### AC-003 — Local Keycloak end-to-end flow

Given an explicitly provisioned local Keycloak user and a valid `elms-frappe` client, when the user clicks the Frappe button, submits the Keycloak local credential and returns through the callback, then Frappe has an authenticated session, a linked `sub`, the expected default roles and a redirect to `/app`.

### AC-004 — Yandex broker end-to-end flow

Given non-empty Yandex credentials in the ignored env file and the Yandex app registered with the Keycloak broker callback, when the user chooses Yandex on Keycloak and completes consent, then Keycloak creates/links the realm user and Frappe creates/links the User by Keycloak `sub`; Frappe never calls a Yandex endpoint directly.

### AC-005 — Fail closed

Given missing Keycloak credentials in dev, the Social Login Key is disabled and no button is rendered. Given missing required credentials in prod, `create-site` exits non-zero before a broken SSO control can be served. Given OAuth denial/state mismatch/token error/missing role, no authenticated session is created.

### AC-006 — No secret leakage

Given the repository and generated realm/site config templates, when bounded scans and sanitized Compose inspection run, then no real Keycloak/Yandex secret is tracked, no secret is printed in settings errors/logs, and Yandex secrets are absent from Frappe `site_config.json`.

### AC-007 — Existing RBAC remains intact

Given a newly brokered or local user, when Frappe creates the user, then default SSO roles are applied through the existing hook. A direct Frappe permission check still denies access when the role is absent; UI visibility is not used as authorization.

---

## Negative / boundary cases

| ID | Condition | Expected behavior | Test map |
|---|---|---|---|
| BN-001 | `KEYCLOAK_CLIENT_SECRET` empty, dev | `enable_social_login=0`, no button, no hidden 500 | TM-001 |
| BN-002 | `ELMS_SSO_REQUIRE=1` with missing Keycloak credential | create-site/config validation exits non-zero | TM-002 |
| BN-003 | `YANDEX_CLIENT_ID` or secret empty | Yandex broker disabled/not selectable; local Keycloak path remains honest; no fake success | TM-003 |
| BN-004 | direct Frappe `yandex` provider row/config appears | ensure/test fails; row is removed/forbidden | TM-004 |
| BN-005 | public URL accidentally set to `http://keycloak:8080` | config validation/contract test fails; browser never receives container hostname | TM-005 |
| BN-006 | OAuth state mismatch or user denies consent | no session; standard Frappe error path | TM-006 |
| BN-007 | token has no usable email or required role missing | signup fails closed; no partially authenticated user | TM-007 |
| BN-008 | repeated migrate/import | one Social Login Key, one realm/client/broker identity config; no duplicate button | TM-008 |
| BN-009 | Yandex unavailable but user has no explicit local credential | Keycloak rejects local login; no automatic password generation | TM-009 |
| BN-010 | CSS asset absent or cache stale | live smoke/build evidence fails; docs require asset build and clear-cache | TM-010 |

---

## Design translation contract

The Neftegaz visual language is transferred as a small, bounded contract:

1. Use `#f5f7fa` paper, white surface, graphite text and cobalt action as the dominant light service palette.
2. Use compact 4px spacing rhythm, 14px base control text, 44px control height and 3px radius from the rendered Neftegaz components.
3. Keep one primary action, no gradient, no dashboard-card wall, no decorative animation and no copied portal logo/brand.
4. Preserve Frappe's information architecture and generated social-login anchor; styling cannot replace the auth contract.
5. Scope every selector to login page classes. A global reset, global `:root` token replacement or upstream Frappe template edit is out of scope.
6. Provide default/hover/focus-visible/active/disabled and reduced-motion states. Focus is a required state even though the source project intentionally prioritizes mouse interaction.
7. Do not load remote font/icon resources for a login action. An existing Social Login Key icon may be reused only if it is local, accessible and does not add a second provider impression.

---

## Environment and Docker matrix

| Variable | Dev source | Prod source | Consumer | Rule |
|---|---|---|---|---|
| `KEYCLOAK_CLIENT_ID` | `docker/.env.dev` | deployment `.env` | create-site, backend, Keycloak realm | default `elms-frappe` only for dev |
| `KEYCLOAK_CLIENT_SECRET` | ignored `.env.dev` | required secret | create-site, backend, Keycloak realm | never commit/log; prod required |
| `KEYCLOAK_PUBLIC_URL` | `http://127.0.0.1:8480` | `https://auth.example.com`-like | create-site/backend/Frappe Social Login Key | browser-visible; HTTPS in prod |
| `FRAPPE_PUBLIC_URL` | `http://elms.localhost:8082` | `https://elms.example.com` | Keycloak root/base/redirect URLs | must match browser host |
| `YANDEX_CLIENT_ID` | ignored `.env.dev` | deployment secret store/.env | Keycloak only | empty means broker unavailable |
| `YANDEX_CLIENT_SECRET` | ignored `.env.dev` | deployment secret store/.env | Keycloak only | never enter Frappe `site_config` |
| `ELMS_SSO_DEFAULT_ROLES` | `Desk User, ELMS LMS User` | explicit approved list | typed settings/site config | parse as list; Frappe role names are SoT |
| `ELMS_SSO_REQUIRE` | `0` | `1` | create-site/settings | true is fail-fast |

The `.env` file is read by Docker Compose substitution and service `environment`; the Python process does not read a host-only file path. This keeps local and production behavior identical at the service boundary.

---

## Architecture / wire journey

```mermaid
sequenceDiagram
    actor User
    participant Browser
    participant Frappe as Frappe /login
    participant Keycloak
    participant Yandex
    participant Site as Frappe callback/session

    User->>Browser: Open /login
    Browser->>Frappe: GET /login
    Frappe-->>Browser: One Keycloak anchor + scoped CSS
    User->>Browser: Click Login with Keycloak
    Browser->>Keycloak: GET /realms/elms/.../auth (state, redirect_uri)
    alt Yandex selected
        Keycloak->>Yandex: OIDC authorize/token/userinfo
        Yandex-->>Keycloak: claims
        Keycloak->>Keycloak: first-broker-login / link realm user
    else local fallback selected
        User->>Keycloak: Explicit local credential
    end
    Keycloak-->>Browser: redirect with code
    Browser->>Site: GET /api/method/.../login_via_keycloak
    Site->>Keycloak: token/userinfo by standard Frappe provider
    Keycloak-->>Site: claims with immutable sub
    Site->>Site: find/create User; assign default roles; create session
    Site-->>Browser: redirect /app
```

### Contract registry

| Boundary ID | Method/path or config | Input | Output | Typed failure | Role/auth |
|---|---|---|---|---|---|
| `B-LOGIN` | `GET /login` | browser request, optional safe redirect | HTML login page | no enabled provider → standard password form/no SSO; malformed config → no broken link | Guest/public |
| `B-AUTH` | `GET {KEYCLOAK_PUBLIC_URL}/realms/elms/protocol/openid-connect/auth` | client ID, state, redirect URI, scope | Keycloak login page | invalid client/redirect → Keycloak error, no Frappe session | public authorization start |
| `B-BROKER` | Keycloak `/realms/elms/broker/yandex/endpoint` | Yandex OIDC code/claims | Keycloak realm identity | upstream denial/invalid credentials → Keycloak failure | Yandex/Keycloak boundary |
| `B-CALLBACK` | `GET /api/method/frappe.integrations.oauth2_logins.login_via_keycloak` | `code`, `state`, provider redirect | Frappe session + safe redirect | state/token/email/role error → error/no session | public callback, state-bound |
| `B-CONFIG` | `inject_sso_site_config` via `bench execute` | typed process env | site config with `keycloak_login` and roles | required env missing → ValueError/non-zero | operator/runtime bootstrap |

### Error vocabulary

| Error class | Source | Observable result | Must not happen |
|---|---|---|---|
| `SsoConfigurationError` | typed settings/create-site | non-zero bootstrap with actionable variable name | a button that leads to hidden 500 |
| `ProviderUnavailable` | Frappe login provider filter | SSO button absent and standard login remains | direct Yandex fallback or fake link |
| `OAuthStateError` | Frappe callback | no session, standard error/log-safe diagnostic | accepting callback without state |
| `OAuthExchangeError` | Frappe/Keycloak | no session, no partial success | treating token failure as authenticated |
| `SsoIdentityError` | missing email/sub/role | signup/link rejected | partially created user with empty roles |
| `YandexBrokerError` | Keycloak upstream | Keycloak error page/no Frappe session | Frappe making a direct Yandex call |

---

## Ownership matrix

| Surface | Primary owner | Scope | Required evidence |
|---|---|---|---|
| Product contract and mixed done criterion | APP | one epic owns button, config, wire and journey | plan + decompose traceability |
| Frappe login asset/hook | APP/FRONT surface | `elms/elms/public/css/login.css`, `elms/elms/hooks.py`; no upstream template | rendered HTML + scoped CSS/static scan |
| Frappe SSO config/callback invariants | APP/BACK surface | reuse/fix T-B03 `conf.py`, `settings.py`, `ensure.py`, tests | bench tests + negative provider tests |
| Docker env propagation | APP/DEVOPS surface | compose examples, create-site/backend/keycloak env and docs | sanitized compose/config + prod fail-fast |
| Keycloak realm/Yandex | APP/BACK surface | realm import, public redirect, broker mappers, credentials | discovery/broker/live smoke/manual Yandex |
| Browser/wire acceptance | APP parent | real click, local fallback and configured Yandex broker | named APP QA lanes; no child browser runner |
| Workspaces/Desk navigation | T-F01 | not changed by this epic | separate FRONT plan; no duplicate login work |

### Reconciliation rule for T-F01

`T-F01` remains in the Front queue for Operations/LMS/Settings Workspaces and role visibility. Its requirements about the `/login` SSO label, login CSS/icon and login stages are covered by `T-A01`; before `APP DECOMPOSE`/implementation they must be treated as superseded/reconciled, not executed as a second login implementation. No INTEG child epic is created.

---

## Files / implementation delta

The implementation shard is expected to touch only files justified by this contract:

| Path | Expected change |
|---|---|
| `elms/elms/public/css/login.css` | add scoped Neftegaz-derived login/button tokens and states |
| `elms/elms/hooks.py` | include `/assets/elms/css/login.css` through Frappe hook while preserving existing hooks |
| `elms/elms/sso/settings.py` | typed env adapter with `pydantic-settings`/`SecretStr`; `conf.py` delegates to it |
| `elms/elms/sso/conf.py` | wire typed settings into existing site-config injection; preserve public API/tests |
| `elms/pyproject.toml` | declare compatible `pydantic-settings` dependency if not already provided by runtime |
| `elms/elms/tests/test_login_ui.py` | Frappe-style rendered login/config contract tests |
| `elms/elms/tests/test_sso_config.py` | typed settings, env propagation and fail-closed branches |
| `elms/elms/tests/test_sso_ensure.py` / `test_sso.py` | only missing callback/provider/role assertions; keep existing coverage |
| `docker/compose.dev.yaml` | verify/fix env propagation for create-site/backend/keycloak; no secret literals |
| `docker/compose.prod.yaml` | verify/fix required env and HTTPS/fail-fast constraints |
| `docker/keycloak/realm-elms.json` | verify/fix env-substituted broker/client/import behavior and bounded redirects |
| `docker/keycloak/entrypoint.sh` | render the env-backed realm import safely and fail on partial Yandex credentials |
| `docker/.env.dev.example` | safe development variable contract and placeholders |
| `docker/.env.prod.example` | required production variable contract without values |
| `docker/README.md` | env → Docker → Yandex broker/local fallback runbook |
| `scripts/live_smoke.sh` | add login CSS/single-button/container-host negative assertions if absent |
| `memory-bank/app/plan/T-A01-elms-keycloak-login-ui/md/manual-ac.md` | optional manual evidence checklist only if browser lane is manual |

No implementation writes to `frappe/frappe/**`, no custom auth endpoint, no Vue/React frontend, no separate `memory-bank/integration` epic.

---

## Test map

| ID | Lane | Test | Evidence |
|---|---|---|---|
| TM-001 | backend | `test_sso_config` with missing Keycloak secret | Social Login Key disabled; no direct Yandex config |
| TM-002 | backend/live | prod-like `ELMS_SSO_REQUIRE=1` missing secret | create-site/config exits non-zero |
| TM-003 | backend/live | Keycloak entrypoint with both/none/partial Yandex env branches | broker disabled for none, enabled for both, bootstrap fails for partial; Frappe site config never stores Yandex secret |
| TM-004 | backend | ensure and negative provider tests | exactly one Keycloak row; no `yandex` row/provider |
| TM-005 | wire_journey/live | public URL assertion | generated href/issuer never contains `keycloak:8080` |
| TM-006 | backend | callback state/token failure contract | no session on invalid/denied flow |
| TM-007 | backend | User creation/default role failure branch | role exists or signup throws; no empty-role success |
| TM-008 | backend | repeated ensure/migrate/import | idempotent single provider/client/broker config |
| TM-009 | wire_journey | local Keycloak browser flow | click → Keycloak → callback → `/app` with session |
| TM-010 | frontend_build/live | build and asset inclusion | CSS is emitted and loaded on `/login` |
| TM-011 | browser/manual | visual state checklist | palette, geometry, hover/focus/active and reduced motion |
| TM-012 | leftover_sot | bounded `rg` scans | no direct Frappe Yandex route, real secret or custom auth path |
| TM-013 | wire_journey/manual | configured Yandex broker flow | Keycloak links identity; Frappe sees Keycloak `sub`; no direct Yandex call |

### APP QA charter

| Lane | Required | Command/evidence | Scope / rule |
|---|---:|---|---|
| `backend` | yes | `bench --site <site> run-tests --app elms --module elms.elms.tests.test_login_ui` plus targeted SSO modules | Frappe runner only; `bin/pytest` is not APP backend evidence |
| `frontend_build` | yes | `bench build --app elms` and verify generated login CSS asset | Frappe asset pipeline, no invented npm app |
| `wire_journey` | yes | parent-run live HTML + local Keycloak browser/manual flow | must exercise production `/login` and callback, not resolver-only |
| `live_smoke` | yes | `timeout -k 10s 300s bash scripts/live_smoke.sh` | live HTTP; mocks/ASGI do not count |
| `leftover_sot` | yes | bounded scans from TM-012 | negative old-path checks must be interpreted with bounded scope |
| `browser` | conditional/manual | parent-only browser evidence when runtime is available; otherwise `manual-ac.md` | no child runs browser; absence of browser evidence leaves visual AC unresolved |
| `behavior_smoke` | no | covered by wire/live lanes | not a substitute for required lanes |
| `exploratory` | optional | visual/manual notes | may add evidence, cannot waive required failures |

`PASS` requires every required lane. A green backend suite without rendered `/login`, asset, callback and live evidence is not done.

---

## Implementation outline

L1 means `sNN_cap=1`; backend config, frontend CSS, Docker/env, Keycloak broker verification, wire and targeted tests remain in one mixed implementation shard because they implement one login outcome. Layer-first split into BACK/FRONT/INTEG epics is forbidden.

### s01 — `keycloak-login-vertical-slice`

**Outcome:** an operator can configure env, open the styled standard Frappe login, complete Keycloak local/Yandex path and land in `/app` with existing SSO/RBAC behavior.

**Coverage:** FR-001…FR-008, US-001…US-008, AC-001…AC-007, BN-001…BN-010, TM-001…TM-013.

**Produces:**

- scoped login CSS and Frappe asset hook;
- typed env → existing Frappe site-config adapter;
- Docker dev/prod env propagation and fail-fast checks;
- Keycloak realm/client/Yandex broker configuration using env only;
- no direct Yandex Frappe provider;
- Frappe rendered-login, settings, callback/role and negative tests;
- live smoke assertions and operator manual AC when browser automation is unavailable;
- README path from `.env` to successful login.

**Required verification checkpoints:**

1. configured `/login` renders exactly one accessible Keycloak control with public href and loaded CSS;
2. disabled/missing config renders no broken SSO control or fails fast as configured;
3. local Keycloak credential completes the real callback and creates a Frappe session;
4. Yandex credentials are consumed only by Keycloak and brokered callback works when external setup is available;
5. `sub` identity and default roles remain enforced;
6. no real secret, direct Yandex provider, container-only URL or custom auth stack remains in production scope;
7. all required APP QA lanes are executed by the parent.

**Wire-complete requirement:**

- call sites: standard Frappe `/login` provider renderer and `login_via_keycloak` callback;
- enforce path: `ensure_social_login_keys`/site config disables provider or fails fast when required, and Frappe callback rejects invalid OAuth;
- dual-path scan: no direct Frappe Yandex provider/route and no container-only public issuer;
- instruction scan: README/plan teach Keycloak broker only, not direct Frappe→Yandex;
- `deny_old_proven: true` only after the negative tests and bounded scans pass.

---

## Out of scope / explicit non-goals

- Vue/React login SPA or Frappe template fork.
- New FastAPI/Flask/Starlette endpoint, custom OAuth client or custom session store.
- Direct Frappe→Yandex Social Login Key, direct Yandex callback, SCIM or bulk directory import.
- Copying Yandex passwords/tokens into Keycloak or Frappe.
- Workspaces, Section DocTypes, Desk shell and role navigation from T-F01.
- Product domain screens for Operations/LMS.
- Global Frappe theme rewrite, dark mode, mobile app, Neftegaz logo/brand copying or remote fonts.
- Automatic password creation for every brokered user.
- Live Yandex credentials in repository, fixtures, realm JSON or site config.
- Separate INTEG queue/epic.

---

## Replacement / sunset

### Runtime

`n/a`: there is no legacy auth runtime to replace. The single Frappe Social Login Key `Keycloak` and standard Frappe callback remain the SoT. The new CSS replaces only the stock visual treatment of the existing control, not its markup or behavior.

### Plan reconciliation

The login-related portion of `T-F01-elms-desk-sections-roles` is superseded/reconciled into this APP epic. T-F01 must not add a second login button, provider row, CSS surface or login test as its own outcome; it continues with Workspaces and role-filtered Desk navigation.

### Forbidden after implementation

- two Frappe SSO buttons for Keycloak and Yandex;
- `yandex_login` or a direct Yandex callback in Frappe;
- `http://keycloak:8080` in browser-visible auth URL;
- optional/soft Keycloak path after prod cutover;
- CSS-only authorization or user-facing success without a real callback/session;
- a plan/decompose step that produces only realm metadata without the `/login` → callback → `/app` outcome.

---

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| Frappe assets are cached | build app asset, clear cache, assert loaded asset in live smoke |
| Frappe standard class changes in a future version | test rendered class/href against current Frappe v15 source; keep selector narrowly scoped and document upgrade check |
| Keycloak public/container URL confusion | explicit `KEYCLOAK_PUBLIC_URL` contract, live negative assertion for `keycloak:8080`, prod HTTPS validation |
| Yandex credentials absent in dev | explicit disabled/unavailable state and local fallback runbook; no fake green Yandex result |
| pydantic dependency conflicts with Frappe | pin compatible range, run bench tests in the real image before implementation completion |
| Social Login Key has encrypted secret behavior | test through Frappe Document/bench runtime, not only a plain JSON fake |
| T-F01 duplicate work | queue/plan reconciliation and one APP owner for login; T-F01 remains workspace-only |
| Browser stack unavailable | required live/wire/HTML evidence plus explicit manual AC; no claim of visual PASS without parent evidence |

---

## Done criterion

APP epic is done only when all conditions hold:

1. A configured Docker environment reads Keycloak/Yandex variables from ignored env and imports the `elms` realm.
2. `/login` renders one accessible cobalt Keycloak button in the Neftegaz-derived style, with no direct Yandex button.
3. Clicking it reaches the public Keycloak issuer, never a container-only URL.
4. Local Keycloak fallback completes the real Frappe callback and opens `/app`.
5. Configured Yandex broker completes the same callback when external credentials/setup are available; otherwise the gap is explicit and fail-closed.
6. New identity is linked by Keycloak `sub`, default roles are enforced and Frappe permissions remain authoritative.
7. Missing required config fails closed; no broken button, fake session or secret leak exists.
8. Backend, frontend build, wire journey, live smoke and leftover-SoT lanes pass; browser visual evidence is present or an explicit manual AC artifact records the unavailable automation.
9. T-F01 has no remaining independent login implementation obligation.

### Next phase

`APP DECOMPOSE T-A01-elms-keycloak-login-ui` with one `s01` mixed shard. Do not create BACK/FRONT/INTEG child epics for this outcome.
