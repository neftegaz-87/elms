# [T-B03 | elms-sso-keycloak-yandex] PLAN

**Дата:** 2026-10-28  
**Режим:** BACK PLAN  
**Уровень:** L3  
**Статус:** active  
**Clarify:** Phase 0 skipped — Keycloak+Yandex locked chat 2026-10-28  
**Prompt:** [md/prompt.md](prompt.md)  
**Queue:** `memory-bank/back/roadmap/queue.yaml` → `T-B03` / `T-B03-elms-sso-keycloak-yandex`  
**Batch:** `elms-foundation`  
**Deps:** `T-B01`, `T-B02`  
**Unlocks:** `T-F01-elms-desk-sections-roles` (SSO buttons labels/icons)  
**Skills (Phase 1):** writing-plans · frappe Social Login Key · oauth  
**SUSPENSION GUARD:** active — plan output unlimited (§0.0)

---

## MULTI-EPIC PLAN — 3 эпика (batch `elms-foundation`)

| Queue id | epic_id | Ось | Deps |
|----------|---------|-----|------|
| T-B01 | T-B01-elms-docker-bootstrap | Docker + Keycloak container | — |
| T-B02 | T-B02-elms-roles-rbac | Roles incl. ELMS LMS User | T-B01 |
| T-B03 | T-B03-elms-sso-keycloak-yandex | Social Login Key wiring | T-B01, T-B02 |

---

## Context consumed

| Path | Что вошло |
|------|-----------|
| Chat 2026-10-28 | Keycloak + Yandex SSO; default roles earlier |
| `frappe/frappe/integrations/doctype/social_login_key/` | Provider Keycloak + Custom |
| `frappe/frappe/integrations/oauth2_logins.py` | `login_via_keycloak`, `custom/<provider>` |
| `frappe/frappe/utils/oauth.py` | get_oauth_keys from conf `{provider}_login` |
| T-B01 | Keycloak service + realm stub path |
| T-B02 | Roles exist; Desk User note |

---

## Delivery closure

| Capability / outcome | Classification | Production entrypoint and caller | Success / failure enforcement | Independent outcome test | Foundation approval / follow-up |
|---|---|---|---|---|---|
| Keycloak OIDC login via Social Login Key | `vertical_slice` | `/login` → authorize Keycloak → `/api/method/frappe.integrations.oauth2_logins.login_via_keycloak` | missing client_secret → login provider misconfig throw / button disabled path documented; no fake session | Given Keycloak up + keys in site_config; When OAuth code flow; Then Frappe User session | FRONT labels T-F01 |
| Yandex OAuth login via Custom provider | `vertical_slice` | `/login` → Yandex → `/api/method/frappe.integrations.oauth2_logins.custom/yandex` | same secret policy | Given Yandex app credentials; When code flow; Then User session (manual e2e OK) | FRONT |
| SSO signup default role | `vertical_slice` | hook/patch after social signup → add `ELMS LMS User` + `Desk User` | if default role missing → frappe.throw | Given new social user; When signup Allow; Then roles present or throw | — |

---

## Technology axiom (replace-not-wrap)

| Выбор | Machine input | FORBIDDEN после эпика |
|-------|---------------|------------------------|
| Frappe Social Login Key SoT | DocType rows `keycloak`, `yandex` | custom Flask/FastAPI OAuth; raw rauth outside utils.oauth |
| Credentials via `frappe.conf` | `keycloak_login` / `yandex_login` dicts `{client_id, client_secret}` from site_config.json generated at create-site/boot | plaintext secrets in fixtures JSON committed |
| Keycloak provider type | `social_login_provider=Keycloak` | reinvent endpoints manually unless Keycloak preset insufficient — then still Social Login Key fields |
| Yandex as Custom | authorize/token/api URLs below | Google-as-proxy; undocumented endpoints |
| Fail-closed default role | ensure role exists before append | signup with empty roles list |

---

## Продуктовая спека (WHAT)

Сотрудник открывает `/login`, нажимает «Keycloak» или «Яндекс», проходит IdP, возвращается в ELMS под Frappe User. В dev новые пользователи получают роль LMS по умолчанию (безопасный узкий доступ), Admin назначает ERP/Admin вручную. Секреты приложений не лежат в git.

---

## Product probe

| # | Question | Decision |
|---|----------|----------|
| 1 | Reframe | Нужен базовый SSO без своего IdP-кода |
| 2 | Narrowest wedge | Social Login Key ×2 + conf keys + default role hook |
| 3 | Pre-mortem | secrets in fixtures; signup without roles | conf + throw |
| 4 | Appetite | 2–3d; live Yandex may be manual |

---

### User Stories

| # | Story | Priority | Independent Test |
| :--- | :--- | :--- | :--- |
| US-001 | Как пользователь, я вижу SSO-кнопки когда провайдеры enabled и сконфигурированы. | P0 | `/login` HTML/API provider list contains keycloak & yandex when enabled |
| US-002 | Как пользователь, я логинюсь через Keycloak code flow. | P0 | Manual/e2e: session after callback |
| US-003 | Как пользователь, я логинюсь через Яндекс. | P0 | Manual e2e with real app credentials |
| US-004 | Как система, я не храню client_secret в репозитории. | P0 | `rg` secrets patterns in tracked files = 0 for yandex/keycloak secrets |
| US-005 | Как новый SSO-user (dev), я получаю ELMS LMS User + Desk User. | P0 | after signup roles assert; missing role → throw |
| US-006 | Как Admin, я могу запретить signup (sign_ups=Deny) для провайдера в prod-like config. | P1 | documented; fixture/env switch |

#### Acceptance Scenarios

**US-001:** Given Social Login Key enable_social_login=1 and client_id set; When GET `/login`; Then provider buttons rendered (Frappe social logins partial).

**US-002:** Given Keycloak realm client redirect URI matches site; When authorize→consent→callback; Then logged in User with email from token/userinfo.

**US-003:** Given Yandex OAuth app redirect URI `https://SITE/api/method/frappe.integrations.oauth2_logins.custom/yandex` (or http for local); When flow completes; Then session.

**US-004:** Given clean git tree; When scan; Then no real secrets; only env example placeholders.

**US-005:** Given sign_ups=Allow; When first login new subject; Then User has roles Desk User + ELMS LMS User OR throw if role missing.

**US-006:** Given sign_ups=Deny and unknown user; When callback; Then SignupDisabledError / Frappe deny (stock behavior).

---

### Functional Requirements (FR-###)

- **FR-001:** Довести `docker/keycloak/realm-elms.json`:
  - realm `elms`
  - client `elms-frappe` (confidential)
  - redirect URIs: `http://elms.localhost:${HTTP_PUBLISH_PORT}/api/method/frappe.integrations.oauth2_logins.login_via_keycloak` и variant without port if needed; `http://127.0.0.1:...` optional for dev
  - web origins: site origin
  - client secret from env substitution **or** documented static dev secret only in `.env.dev` not in realm file committed as real prod secret — **dev:** realm import may use placeholder secret synced via keycloak realm + site_config same value from `.env.dev`
- **FR-002:** Boot/configurator/create-site script sets site_config:
  ```json
  "keycloak_login": {"client_id": "...", "client_secret": "..."},
  "yandex_login": {"client_id": "...", "client_secret": "..."},
  "elms_sso_default_roles": ["Desk User", "ELMS LMS User"]
  ```
  Missing required keys for an **enabled** provider → enable_social_login must stay 0 **or** explicit throw at ensure time (не «кнопка ведёт в 500 без причины»). **Решение:** `ensure_social_login_keys()` включает enable только если conf keys present; иначе документ disabled + log/raise in migrate if `ELMS_SSO_REQUIRE=1`.
- **FR-003:** Social Login Key `keycloak`:
  - provider_name / name scrubbed `keycloak`
  - social_login_provider = Keycloak
  - base_url = Keycloak realm URL e.g. `http://keycloak:8080/realms/elms` (internal) — **внимание:** browser redirect должен использовать публичный URL `http://localhost:KEYCLOAK_PUBLISH_PORT/realms/elms` в authorize_url для browser. Зафиксировать **public** base_url в Social Login Key (`http://elms.localhost` host-gateway / `http://127.0.0.1:$KEYCLOAK_PUBLISH_PORT`).
  - redirect_url = `/api/method/frappe.integrations.oauth2_logins.login_via_keycloak`
  - enable_social_login = 1 when conf present
  - sign_ups = Allow (dev)
  - client_id may be empty in DocType if conf supplies keys (Frappe get_oauth_keys prefers conf)
- **FR-004:** Social Login Key `yandex`:
  - social_login_provider = Custom
  - custom_base_url = 0 (absolute URLs)
  - authorize_url = `https://oauth.yandex.ru/authorize`
  - access_token_url = `https://oauth.yandex.ru/token`
  - api_endpoint = `https://login.yandex.ru/info`
  - api_endpoint_args / auth_url_data JSON as required by Yandex (`format=json` query — via api_endpoint_args `{"format":"json"}` or endpoint with query)
  - user_id_property = `id`
  - redirect_url = `/api/method/frappe.integrations.oauth2_logins.custom/yandex`
  - auth_url_data: `{"response_type":"code"}` (+ scope if needed: `login:email login:info`)
  - icon/label friendly for FRONT
- **FR-005:** Implement `elms/elms/sso.py` (or `elms/elms/auth/sso.py`):
  - `ensure_social_login_keys()`
  - `on_user_after_insert` or Frappe social signup hook / override path — найти канонический extension point (`after_insert` on User when `social_logins` / `frappe.utils.oauth` signup). **Решение implement:** doc_events User `after_insert` + check if created via social (flags / Social Login User child) → `add_roles(*default_roles)`; if role missing `frappe.throw`.
- **FR-006:** Wire `after_migrate` / `after_install` to ensure Social Login Key docs (idempotent).
- **FR-007:** Tests:
  - unit: ensure creates DocTypes Social Login Key with expected redirect URLs
  - unit: enable stays 0 without conf secrets
  - unit: default role assign / throw
  - static: no secrets in repo
- **FR-008:** Manual checklist in plan/README: Keycloak user create, Yandex app create at oauth.yandex.ru, redirect URI register.
- **FR-009:** Document host networking: browser→Keycloak public port; Frappe container may need `extra_hosts` already from T-B01.

### Yandex field mapping notes

Yandex `login.yandex.ru/info` returns `id`, `login`, `default_email`, `emails`. Frappe oauth user creation uses email — verify `frappe.utils.oauth` email extraction; if only `default_email`, may need `user_id_property` + patch/hook to set email from `default_email` if stock mapping fails. **If stock fails:** in-epic thin adapter hook — still через Social Login Key, не новый OAuth stack; throw if email absent (no account without email).

### Success Criteria

| ID | Результат | Проверка |
|----|-----------|----------|
| SC-001 | Social Login Key rows | exists keycloak, yandex |
| SC-002 | Conf-gated enable | unit |
| SC-003 | Default roles | unit |
| SC-004 | No secrets in git | rg |
| SC-005 | Manual Keycloak login | checklist |
| SC-006 | Manual Yandex login | checklist |

### Assumptions

- T-B01 Keycloak container healthy.
- T-B02 roles seeded before SSO signup test.
- Developer can create Yandex OAuth application.

### Clarifications

- Default role = `ELMS LMS User` + `Desk User` (chat + Desk access).
- sign_ups Allow in dev example; Deny documented for prod.
- Account linking edge cases (same email password user) = stock Frappe behavior; out of deep UX.

## AC

1. ensure_social_login_keys idempotent.
2. Keycloak + Yandex redirect URLs exact.
3. Conf secrets drive client_id/secret.
4. Enable only when conf present (default).
5. Signup default roles fail-closed.
6. Manual checklist documented.
7. AC− no custom OAuth server; no secrets in git.

### AC−

1. Нет committed client_secret реальных значений.
2. Нет второго OAuth implementation module duplicating oauth2_logins.
3. Нет signup success with zero ELMS roles when default configured.
4. Нет hard dependency on ERPNext social patches.

## Boundary / negative cases

| ID | Class | Input / condition | Expected | Maps TM |
|----|-------|-------------------|----------|---------|
| BN-001 | misconfig | no yandex_login conf | yandex enable=0 or ensure skip enable | TM-001 |
| BN-002 | misconfig | Keycloak down mid-login | IdP/browser error; Frappe no fake session | TM-002 |
| BN-003 | authz/signup | sign_ups Deny + new user | deny | TM-003 |
| BN-004 | empty | userinfo without email | throw clear | TM-004 |
| BN-005 | missing role | ELMS LMS User deleted | throw on signup assign | TM-005 |
| BN-006 | wrong redirect | bad URI in Keycloak client | IdP error visible | TM-006 |

## Техника / архитектура (HOW)

### Sequence Keycloak

```text
Browser GET /login
  -> click Keycloak
  -> redirect authorize_url (public Keycloak)
  -> user auth
  -> redirect login_via_keycloak?code&state
  -> frappe.utils.oauth.login_via_oauth2("keycloak", ...)
  -> get_oauth_keys from conf keycloak_login
  -> create/login User
  -> elms default role hook
  -> Desk session
```

### Sequence Yandex

```text
Browser -> Yandex authorize
  -> custom/yandex callback
  -> login_via_oauth2("yandex", ...)
  -> conf yandex_login
  -> User + default roles
```

### Code paths

```text
elms/elms/sso/
  ensure.py       # Social Login Key upsert
  roles.py        # default roles on social signup
  constants.py    # provider names, URLs
elms/elms/hooks.py
  after_migrate += ensure
  doc_events User after_insert → maybe_assign_sso_roles
```

### Env keys (`.env.dev.example`)

```text
KEYCLOAK_CLIENT_ID=elms-frappe
KEYCLOAK_CLIENT_SECRET=change-me
KEYCLOAK_PUBLIC_URL=http://127.0.0.1:8083
YANDEX_CLIENT_ID=
YANDEX_CLIENT_SECRET=
ELMS_SSO_DEFAULT_ROLES=Desk User,ELMS LMS User
ELMS_SSO_REQUIRE=0
```

## Eng review spine

### Data flow

```text
[env] -> [site_config *_login] -> [Social Login Key enable]
[IdP] -> [oauth2_logins callback] -> [User] -> [default roles] -> [session]
```

### Failure matrix

| Component | Failure | Detection | Response | Test ID |
|-----------|---------|-----------|----------|---------|
| conf | missing | ensure | enable=0 | TM-001 |
| IdP | down | browser/HTTP | no session | TM-002 |
| signup | Deny | SignupDisabledError | deny | TM-003 |
| email | missing | validate | throw | TM-004 |
| role | missing | exists check | throw | TM-005 |

### Eng spine self-check

| Dimension | Score | Gap |
|-----------|-------|-----|
| Data flow | 5 | — |
| Failure | 5 | — |
| Testability | 4 | live IdP manual |

## Replacement / sunset

| Устаревает | Замена |
|------------|--------|
| T-B01 realm stub empty client | full client redirect URIs |
| Password-only mental model | SSO alongside password (Administrator may stay password) |

deletes: n/a greenfield SSO module.

## Test map (TM)

| ID | Type | Assert |
|----|------|--------|
| TM-001 | unit | no conf → not enabled |
| TM-002 | manual | Keycloak stop → no session |
| TM-003 | unit/manual | Deny signup |
| TM-004 | unit | missing email throw |
| TM-005 | unit | missing role throw |
| TM-006 | manual | bad redirect |
| TM-007 | unit | ensure URLs |
| TM-008 | static | rg secrets |

## Manual e2e checklist

1. Start stack; open Keycloak admin; verify realm `elms` client.
2. Create Keycloak user with email.
3. Set `.env.dev` secrets; recreate site_config / restart backend.
4. Open `/login` → Keycloak → return logged in; roles include ELMS LMS User + Desk User.
5. Register Yandex OAuth app; set redirect; set env; ensure yandex; login.
6. Confirm `rg -i 'client_secret|yandex_login' --glob '!.env*' ` no real secrets.

## Implementation stages

| Stage | Delta |
|-------|-------|
| s01 | constants + realm client JSON |
| s02 | site_config injection from env |
| s03 | ensure Social Login Key keycloak+yandex |
| s04 | default roles hook fail-closed |
| s05 | unit tests + secret scan |
| s06 | manual checklist docs |

## Out of scope

- FRONT button copy/icons polish beyond stock (T-F01)
- MFA / Conditional access
- SCIM user provisioning
- Linking multiple IdPs to one User beyond Frappe stock

## Risks

| Risk | Mitigation |
|------|------------|
| Keycloak URL browser vs docker DNS | public URL in Social Login Key |
| Yandex email field mapping | throw if missing; hook map default_email |
| HTTP local redirect blocked by Yandex | document HTTPS tunnel or Yandex test rules |
