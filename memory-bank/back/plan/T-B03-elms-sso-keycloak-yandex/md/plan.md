# [T-B03 | elms-sso-keycloak-yandex] PLAN

**Дата:** 2026-10-28  
**Режим:** BACK PLAN  
**Уровень:** L3  
**Статус:** active  
**Clarify:** Phase 0 skipped — brokered Keycloak→Yandex flow and local Keycloak fallback locked chat 2026-10-29  
**Prompt:** [md/prompt.md](prompt.md)  
**Queue:** `memory-bank/back/roadmap/queue.yaml` → `T-B03` / `T-B03-elms-sso-keycloak-yandex`  
**Batch:** `elms-foundation`  
**Deps:** `T-B01`, `T-B02`  
**Unlocks:** `T-F01-elms-desk-sections-roles` (single Keycloak SSO affordance)  
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
| Brokered Keycloak OIDC login | `vertical_slice` | `/login` → Keycloak → Yandex broker (optional) → `/api/method/frappe.integrations.oauth2_logins.login_via_keycloak` | missing Keycloak client credentials or failed upstream auth produces an explicit failure; no fake session | Given Keycloak and Yandex broker are configured; When the code flow completes; Then Keycloak user/link and Frappe User session exist | FRONT single button |
| Just-in-time identity provisioning | `vertical_slice` | Keycloak first-broker-login → realm user + federated Yandex link → Frappe OAuth callback → Frappe User | no bulk import promise; missing email or denied signup fails closed | Given a new Yandex subject; When it authenticates through Keycloak; Then both identity records are created without a direct Frappe→Yandex path | — |
| Local Keycloak fallback | `vertical_slice` | Keycloak local username/password form → same OIDC client → Frappe session | only users with an explicitly provisioned Keycloak credential can use fallback; Yandex password is never copied | Given Yandex is unavailable and a local Keycloak credential exists; When the user authenticates via Keycloak; Then the same Frappe User session is created | manual runbook |
| SSO signup default role | `vertical_slice` | hook/patch after Keycloak social signup → add `ELMS LMS User` + `Desk User` | if default role missing → frappe.throw | Given signup Allow; When a new brokered user is created; Then roles are present or signup fails | — |

---

## Technology axiom (replace-not-wrap)

| Выбор | Machine input | FORBIDDEN после эпика |
|-------|---------------|------------------------|
| Frappe Social Login Key SoT | One DocType row `keycloak`; Yandex is configured only as a Keycloak Identity Provider | direct Frappe→Yandex login, custom Flask/FastAPI OAuth, or raw rauth outside utils.oauth |
| Credentials via `frappe.conf` | `keycloak_login` dict `{client_id, client_secret}` from site_config.json generated at create-site/boot; Yandex credentials are consumed only by Keycloak | plaintext secrets in fixtures JSON or Frappe `yandex_login` committed |
| Keycloak provider type | `social_login_provider=Keycloak` | reinvent endpoints manually unless Keycloak preset insufficient — then still Social Login Key fields |
| Yandex broker | Keycloak realm `identityProviders[].alias=yandex`, first-broker-login provisioning, Yandex callback terminates at Keycloak | Frappe `social_login_provider=Custom` for Yandex or a second `/login` provider button |
| Local fallback | Explicit Keycloak local credential for selected users, same `elms-frappe` client | copying Yandex passwords, silently generating credentials for every user, or fallback through a direct Frappe password path |
| Fail-closed default role | ensure role exists before append | signup with empty roles list |

---

## Продуктовая спека (WHAT)

Сотрудник открывает `/login` и нажимает единственную кнопку «Войти через Keycloak». Keycloak показывает Yandex 360 как внешний IdP; после первого успешного входа создаёт локальную запись realm и связь с Yandex, а Frappe создаёт локального User. Для выбранных пользователей администратор может заранее или после первого входа установить локальный пароль Keycloak; при недоступности Yandex они входят через ту же страницу Keycloak. В dev новые пользователи получают роль LMS по умолчанию (безопасный узкий доступ), Admin назначает Operations/Admin вручную. Секреты приложений не лежат в git.

---

## Product probe

| # | Question | Decision |
|---|----------|----------|
| 1 | Reframe | Нужен базовый SSO без своего IdP-кода |
| 2 | Narrowest wedge | Keycloak Social Login Key ×1 + brokered Yandex + optional local credential + default role hook |
| 3 | Pre-mortem | secrets in fixtures; signup without roles | conf + throw |
| 4 | Appetite | 2–3d; live Yandex broker and local fallback may be manual |

---

### User Stories

| # | Story | Priority | Independent Test |
| :--- | :--- | :--- | :--- |
| US-001 | Как пользователь, я вижу одну понятную кнопку входа через Keycloak. | P0 | `/login` provider list contains Keycloak and does not expose direct Yandex provider |
| US-002 | Как пользователь, я вхожу через Yandex, открытый внутри Keycloak. | P0 | Manual/e2e: Keycloak broker callback creates session after code flow |
| US-003 | Как оператор, я могу включить локальный пароль Keycloak для выбранного пользователя как fallback. | P0 | Manual: same realm user authenticates without Yandex |
| US-004 | Как система, я не храню client_secret в репозитории. | P0 | `rg` secrets patterns in tracked files = 0 for yandex/keycloak secrets |
| US-005 | Как новый brokered SSO-user (dev), я получаю ELMS LMS User + Desk User. | P0 | after signup roles assert; missing role → throw |
| US-006 | Как Admin, я могу запретить создание новых Frappe Users через Keycloak в prod-like config. | P1 | documented `sign_ups=Deny` behavior |
| US-007 | Как система, я создаю Keycloak users just-in-time при первом входе, а не обещаю полную синхронизацию каталога Yandex. | P1 | first broker login creates/link user; no SCIM/import requirement |

#### Acceptance Scenarios

**US-001:** Given the Keycloak Social Login Key is enabled; When GET `/login`; Then exactly the Keycloak provider is rendered by Frappe and no direct Yandex Social Login Key exists.

**US-002:** Given the Keycloak realm client and Yandex broker callback are configured; When the user chooses Yandex on Keycloak and completes authorize→broker callback→Frappe callback; Then the same Keycloak subject is linked to a Frappe User session.

**US-003:** Given a Keycloak user has an explicitly provisioned local password; When Yandex is unavailable and the user selects local Keycloak login; Then the `elms-frappe` OIDC flow creates the same Frappe User session.

**US-004:** Given clean git tree; When scan; Then no real secrets; only env example placeholders.

**US-005:** Given Keycloak `sign_ups=Allow`; When first broker login creates a new subject; Then Keycloak has the realm user/federated link and Frappe User has roles Desk User + ELMS LMS User OR signup throws if a role is missing.

**US-006:** Given `sign_ups=Deny` and no existing Frappe User; When the Keycloak callback completes; Then Frappe denies local signup with standard behavior.

**US-007:** Given a user has never logged in; When no broker login is performed; Then no promise is made that the user already exists in Keycloak; bulk Yandex directory provisioning remains out of scope.

---

### Functional Requirements (FR-###)

- **FR-001:** Довести `docker/keycloak/realm-elms.json`:
  - realm `elms`
  - client `elms-frappe` (confidential)
  - redirect URIs: `http://elms.localhost:${HTTP_PUBLISH_PORT}/api/method/frappe.integrations.oauth2_logins.login_via_keycloak` и variant without port if needed; `http://127.0.0.1:...` optional for dev
  - web origins: site origin
  - client secret from env substitution **or** documented static dev secret only in `docker/.env.dev` not in realm file committed as real prod secret — **dev:** realm import may use placeholder secret synced via keycloak realm + site_config same value from `docker/.env.dev`
  - Yandex Identity Provider alias `yandex` with broker callback `http://<public-keycloak>/realms/elms/broker/yandex/endpoint`, `first broker login` flow, trusted email, and email/name mappers
  - local Keycloak username/password login remains enabled for explicitly provisioned fallback users; `registrationAllowed=false` blocks public registration but does not disable brokered first-login provisioning
- **FR-002:** Boot/configurator/create-site script from `docker/compose.dev.yaml` sets site_config:
  ```json
  "keycloak_login": {"client_id": "...", "client_secret": "..."},
  "elms_sso_default_roles": ["Desk User", "ELMS LMS User"]
  ```
  Yandex client credentials are passed only to the Keycloak container (`YANDEX_CLIENT_ID` / `YANDEX_CLIENT_SECRET`) and are never exposed as a Frappe `yandex_login` provider. Missing Keycloak credentials → the single Frappe provider remains disabled or the configured `ELMS_SSO_REQUIRE=1` path throws explicitly; no button leads to a hidden 500.
- **FR-003:** Social Login Key `keycloak`:
  - provider_name / name scrubbed `keycloak`
  - social_login_provider = Keycloak
  - base_url = public Keycloak realm URL `${KEYCLOAK_PUBLIC_URL}/realms/elms`; browser must never receive the container-only `http://keycloak:8080` address
  - redirect_url = `/api/method/frappe.integrations.oauth2_logins.login_via_keycloak`
  - enable_social_login = 1 when conf present
  - sign_ups = Allow (dev)
  - `user_id_property = sub` so the immutable Keycloak subject, not a mutable username, identifies the Frappe social login
  - no second Social Login Key row named `yandex`; a negative test must assert this
- **FR-004:** Configure Yandex only inside Keycloak as an OIDC broker:
  - `identityProviders[].alias = yandex`, `providerId = oidc`, and `enabled = true` only when `YANDEX_CLIENT_ID` and `YANDEX_CLIENT_SECRET` are present
  - authorization/token/userinfo URLs remain Yandex-owned and are called by Keycloak, never by Frappe
  - map Yandex `default_email`, `first_name`, and `last_name` to Keycloak email/profile claims; Keycloak returns the normalized claims to Frappe
  - the Yandex application redirect URI is the Keycloak broker endpoint, never `/api/method/frappe.integrations.oauth2_logins.custom/yandex`
  - first successful broker login creates or links the Keycloak realm user and stores the Yandex federated identity; this is just-in-time provisioning, not SCIM or a full directory import
- **FR-005:** Implement the dedicated `elms/elms/sso/` package:
  - `ensure_social_login_keys()` in `elms/elms/sso/ensure.py`
  - Frappe `doc_events` `User.after_insert` hook in `elms/elms/sso/roles.py`; detect the Keycloak social link → `add_roles(*default_roles)`; if role missing `frappe.throw`
  - retain one-way Keycloak→Frappe profile/status/group reconciliation; never write Frappe roles or passwords back to Yandex
- **FR-005a:** Document local fallback credentials:
  - an administrator may set a Keycloak password for a selected realm user through Keycloak Admin Console or an approved reset/invitation flow
  - this is a Keycloak credential, not a Frappe password; the Yandex password/token is never copied or stored in Keycloak by ELMS
  - a broker-created user without a local credential must fail authentication when Yandex is unavailable; a user with an explicit local credential can use the normal Keycloak form and the same `elms-frappe` client
  - fallback provisioning is per-user/role policy, not automatic password creation for every Yandex user
- **FR-006:** Wire `after_migrate` / `after_install` to ensure Social Login Key docs (idempotent).
- **FR-007:** Tests:
  - unit: ensure creates exactly one enabled-capable `keycloak` Social Login Key and no direct `yandex` row
  - unit: enable stays 0 without conf secrets
  - unit: default role assign / throw
  - unit/manual: first broker login provisions Keycloak and Frappe identities; local Keycloak credential works when Yandex is unavailable
  - static: no secrets in repo
- **FR-008:** Manual checklist in plan/README: configure Yandex app with the Keycloak broker callback, complete first-broker-login provisioning, inspect the Keycloak federated link, set a local password for a selected fallback user, and test Yandex outage.
- **FR-009:** Document host networking: browser→Keycloak public port; Frappe container may need `extra_hosts` already from T-B01.
- **FR-010:** The Frappe login page exposes only the Keycloak provider. The Yandex choice and the local-password fallback are Keycloak login-page concerns.
- **FR-011:** No bulk Yandex directory provisioning is promised. A user enters Keycloak/Frappe only after first successful broker login or explicit local Keycloak provisioning.

### Yandex broker mapping notes

Yandex `login.yandex.ru/info` returns `id`, `login`, `default_email`, `emails`. Keycloak maps `default_email` to the realm email and exposes the normalized OIDC `sub`, `email`, `firstName`, and `lastName` claims to Frappe. Frappe must consume the Keycloak claims only; it must not call Yandex `userinfo` directly. If Keycloak receives no usable email, the first-broker-login flow fails explicitly and no Frappe User is created.

### Success Criteria

| ID | Результат | Проверка |
|----|-----------|----------|
| SC-001 | Social Login Key rows | exactly one `keycloak` row; no direct `yandex` row |
| SC-002 | Conf-gated enable | unit |
| SC-003 | Default roles | unit |
| SC-004 | No secrets in git | rg |
| SC-005 | Manual brokered Keycloak→Yandex login | checklist |
| SC-006 | Manual local Keycloak fallback during Yandex outage | checklist |

### Assumptions

- T-B01 Keycloak container healthy.
- T-B02 roles seeded before SSO signup test.
- Developer can create a Yandex OAuth application whose redirect URI is the public Keycloak broker endpoint.
- Selected fallback users may receive explicit local Keycloak credentials; this is an operational policy, not automatic password provisioning.

### Clarifications

- Default role = `ELMS LMS User` + `Desk User` (chat + Desk access).
- `sign_ups=Allow` in dev example; `Deny` documented for prod.
- Yandex is the upstream IdP; Keycloak is the only Frappe-facing IdP.
- Existing Frappe User lookup uses the verified email while the social-login link uses immutable Keycloak `sub`; duplicate/linking edge cases beyond the stock first-broker flow are out of deep UX.
- SCIM/full Yandex directory import is out of scope; provisioning is just-in-time on first broker login.

## AC

1. ensure_social_login_keys idempotent.
2. The only Frappe OAuth redirect is `login_via_keycloak`; the Yandex redirect terminates at the Keycloak broker endpoint.
3. Conf secrets drive client_id/secret.
4. Frappe enables only the Keycloak provider when its conf is present; Yandex credentials gate the Keycloak broker, not a Frappe provider.
5. Signup default roles fail-closed.
6. First broker login creates or links a Keycloak realm user and then a Frappe User; no bulk directory import is implied.
7. An explicitly provisioned local Keycloak credential can authenticate through the same Frappe client while Yandex is unavailable.
8. Manual checklist documented.
9. AC− no custom OAuth server; no secrets in git.

### AC−

1. Нет committed client_secret реальных значений.
2. Нет второго OAuth implementation module duplicating oauth2_logins.
3. Нет signup success with zero ELMS roles when default configured.
4. Нет hard dependency on ERPNext social patches.

## Boundary / negative cases

| ID | Class | Input / condition | Expected | Maps TM |
|----|-------|-------------------|----------|---------|
| BN-001 | misconfig | missing Keycloak credentials or Yandex broker credentials | Keycloak provider/broker stays disabled or configured fail-closed; no direct Yandex button | TM-001 |
| BN-002 | misconfig | Keycloak down mid-login | IdP/browser error; Frappe no fake session | TM-002 |
| BN-003 | authz/signup | `sign_ups=Deny` + new brokered user | Frappe denies local signup | TM-003 |
| BN-004 | empty | Keycloak userinfo without usable email | throw clear; no realm-to-Frappe account | TM-004 |
| BN-005 | missing role | ELMS LMS User deleted | throw on signup assign | TM-005 |
| BN-006 | wrong redirect | bad Yandex→Keycloak broker or Keycloak→Frappe URI | IdP error visible; no session | TM-006 |
| BN-007 | outage | Yandex unavailable and no local Keycloak credential | login fails closed; no fake fallback | TM-009 |
| BN-008 | outage | Yandex unavailable and explicit local Keycloak credential exists | same Keycloak client completes login to existing Frappe User | TM-010 |
| BN-009 | identity | user has never performed broker login and has no local Keycloak account | no automatic Frappe/Keycloak user is promised | TM-011 |

## Техника / архитектура (HOW)

### Sequence Keycloak

```text
Browser GET /login
  -> click the only Frappe provider: Keycloak
  -> redirect to public Keycloak authorize endpoint
  -> Keycloak shows local form and Yandex 360 IdP
  -> choose Yandex (normal path) or local Keycloak credential (fallback)
  -> Yandex -> Keycloak broker callback /realms/elms/broker/yandex/endpoint
  -> Keycloak first-broker-login creates/links realm user and federated identity
  -> Keycloak redirects to Frappe login_via_keycloak?code&state
  -> frappe.utils.oauth.login_via_oauth2("keycloak", ...)
  -> get_oauth_keys from conf keycloak_login
  -> get Keycloak userinfo claims (email, sub, profile, groups)
  -> create/login Frappe User and store provider=keycloak, userid=sub
  -> elms default role hook
  -> Desk session
```

### Sequence local fallback

```text
Browser -> Frappe /login -> Keycloak authorize
  -> local Keycloak username/password form
  -> Keycloak issues the same elms-frappe OIDC code
  -> Frappe login_via_keycloak callback
  -> existing Frappe User + default/session roles
```

### Code paths

```text
elms/elms/sso/
  ensure.py       # only the Frappe-facing Keycloak Social Login Key upsert
  roles.py        # default roles on social signup
  constants.py    # provider names, URLs, config keys
  conf.py         # keycloak_login and default-role site_config injection
elms/elms/hooks.py
  after_migrate += ensure
  doc_events User after_insert → maybe_assign_sso_roles
docker/keycloak/realm-elms.json
  identityProviders[yandex] # upstream broker, not a Frappe Social Login Key
```

### Env keys (`docker/.env.dev.example`)

```text
KEYCLOAK_CLIENT_ID=elms-frappe
KEYCLOAK_CLIENT_SECRET=change-me
KEYCLOAK_PUBLIC_URL=http://127.0.0.1:8480
YANDEX_CLIENT_ID=
YANDEX_CLIENT_SECRET=
ELMS_SSO_DEFAULT_ROLES=Desk User,ELMS LMS User
ELMS_SSO_REQUIRE=0
```

## Eng review spine

### Data flow

```text
[KEYCLOAK_*] -> [site_config keycloak_login] -> [one Frappe Social Login Key]
[YANDEX_*] -> [Keycloak identity provider yandex]
[Yandex or local Keycloak auth] -> [Keycloak realm user/link] -> [Frappe callback]
  -> [Frappe User] -> [default roles] -> [session]
```

### Failure matrix

| Component | Failure | Detection | Response | Test ID |
|-----------|---------|-----------|----------|---------|
| Keycloak/Yandex conf | missing | ensure/realm import | provider or broker disabled; no direct Yandex path | TM-001 |
| Keycloak | down | browser/HTTP | no session | TM-002 |
| signup | Deny | SignupDisabledError | deny | TM-003 |
| email | missing | Keycloak/Frappe validation | throw | TM-004 |
| role | missing | exists check | throw | TM-005 |
| Yandex | down, no local credential | Keycloak login | explicit auth failure | TM-009 |
| Yandex | down, local credential exists | Keycloak login | existing Frappe session | TM-010 |

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
| Direct Frappe→Yandex Social Login Key | Keycloak broker Identity Provider `yandex` |
| Two Frappe SSO buttons | One Frappe Keycloak button; Yandex/local choice belongs to Keycloak |
| Password-only mental model | Brokered SSO plus explicit local Keycloak fallback credential |

deletes: direct Yandex Frappe callback/configuration and any second Frappe Social Login Key row.

## Test map (TM)

| ID | Type | Assert |
|----|------|--------|
| TM-001 | unit | missing Keycloak/Yandex broker conf → no enabled Frappe/broker path |
| TM-002 | manual | Keycloak stop → no session |
| TM-003 | unit/manual | Deny signup |
| TM-004 | unit | missing email throw |
| TM-005 | unit | missing role throw |
| TM-006 | manual | bad Yandex broker or Frappe redirect |
| TM-007 | unit | only Keycloak Social Login Key and canonical redirect |
| TM-008 | static | rg secrets |
| TM-009 | manual | Yandex outage with no local Keycloak credential fails closed |
| TM-010 | manual | Yandex outage with explicit local Keycloak credential succeeds |
| TM-011 | manual/unit | first broker login creates Keycloak link and Frappe User just-in-time |

## Manual e2e checklist

1. Start stack; open Keycloak admin; verify realm `elms`, client `elms-frappe`, and Identity Provider alias `yandex`.
2. Register a Yandex OAuth application with redirect URI `http://<public-keycloak>/realms/elms/broker/yandex/endpoint`; set `YANDEX_CLIENT_ID` and `YANDEX_CLIENT_SECRET` only in the environment.
3. Set the Keycloak client secret and public URLs; recreate site_config / restart backend; verify Frappe has exactly one enabled-capable Social Login Key named `keycloak`.
4. Open `/login` and confirm Frappe shows only «Войти через Keycloak».
5. On the Keycloak page choose Yandex; complete first broker login; verify Keycloak realm user + federated Yandex link, then Frappe User with `Desk User` + `ELMS LMS User`.
6. In Keycloak Admin Console set a local password for a selected fallback user. Stop or block Yandex, choose local Keycloak login, and verify the same Frappe User session.
7. Repeat with a Yandex-only user without a local credential and verify explicit authentication failure.
8. Confirm no direct Frappe Yandex callback/provider exists and no real secrets are tracked.

## Implementation stages

| Stage | Delta |
|-------|-------|
| s01 | Keycloak realm client + Yandex broker + env/site_config injection |
| s02 | one Keycloak-facing Social Login Key + migration hooks; remove direct Yandex path |
| s03 | brokered JIT user/role behavior, local fallback runbook, tests, and secret scan |

## Out of scope

- FRONT button copy/icons polish beyond stock (T-F01)
- MFA / Conditional access
- SCIM user provisioning
- Bulk Yandex directory import and background synchronization
- Automatic local password creation for every brokered user
- Linking multiple external IdPs to one Keycloak User beyond the stock first-broker flow

## Risks

| Risk | Mitigation |
|------|------------|
| Keycloak URL browser vs docker DNS | public URL in Social Login Key |
| Yandex email field mapping | Keycloak mapper for `default_email`; fail closed before Frappe User creation if email is missing |
| Yandex outage | explicitly provision local Keycloak credentials only for approved users; test both credential branches |
| Duplicate identity by mutable username/email | persist Keycloak `sub` in Frappe social login and use verified email only for initial User lookup |
| HTTP local redirect blocked by Yandex | document HTTPS tunnel or Yandex test rules for the Keycloak broker endpoint |
