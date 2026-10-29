# Manual Acceptance Criteria Checklist: Keycloak Login UI (T-A01-elms-keycloak-login-ui)

This document provides operator acceptance verification steps and observable outcomes for the unified Keycloak login vertical slice.

## Overview

- **Epic:** T-A01-elms-keycloak-login-ui
- **Role:** app
- **Scope:** Scoped Neftegaz login CSS asset, typed pydantic-settings SSO adapter, Keycloak single provider login flow, Yandex OIDC broker routing, fail-closed handling, secret hygiene.

---

## Acceptance Matrix

| Item | ID | Scenario | Steps to Verify | Expected Observable Outcome | Status |
|---|---|---|---|---|---|
| 1 | **AC-001** | Configured login button | 1. Configure valid Keycloak settings in `docker/.env.dev`.<br>2. Run `bench migrate` or `create-site`.<br>3. Open `http://elms.localhost:8082/login` in browser. | Single visible `.btn-keycloak` button displayed. Link target starts with public `http://127.0.0.1:8480/realms/elms/...`, never `keycloak:8080`. No direct Yandex button exists on Frappe page. `login.css` asset is loaded. | PASS |
| 2 | **AC-002** | Styled visual states | 1. Inspect `.btn-keycloak` in browser devtools.<br>2. Check normal height (44px) and radius (3px).<br>3. Hover with mouse.<br>4. Tab to focus with keyboard.<br>5. Click and hold (active).<br>6. Emulate `prefers-reduced-motion: reduce`. | - Height: 44px, radius: 3px, color: `#0d4cd3`.<br>- Hover: darkens to `#0a3fb0`.<br>- Focus: 2px outline with 2px offset.<br>- Active: subtle 1px translate.<br>- Reduced motion: transitions disabled. No layout shift. | PASS |
| 3 | **AC-003** | Local Keycloak fallback flow | 1. Click Keycloak login button on `/login`.<br>2. On Keycloak login form, enter `fallback.user` / fallback password.<br>3. Submit login. | Redirects back to `/api/method/frappe.integrations.oauth2_logins.login_via_keycloak`, links user by `sub`, assigns default roles (`Desk User`, `ELMS LMS User`), redirects to `/app`. | PASS |
| 4 | **AC-004** | Yandex broker flow | 1. With configured Yandex broker, click Keycloak login button.<br>2. On Keycloak login page, select "Yandex 360".<br>3. Complete external Yandex consent. | Keycloak brokers user, links identity, and redirects to Frappe. Frappe creates/links user by Keycloak `sub`. Frappe never directly contacts Yandex API. | PASS |
| 5 | **AC-005** | Fail closed on missing config | 1. Set `ELMS_SSO_REQUIRE=0` and empty `KEYCLOAK_CLIENT_SECRET`.<br>2. Load `/login`.<br>3. Set `ELMS_SSO_REQUIRE=1` with empty `KEYCLOAK_CLIENT_SECRET`. | - Dev mode without secret: Social Login Key disabled, no broken button on `/login`.<br>- Require mode: `create-site` or settings validation fails with non-zero exit code. | PASS |
| 6 | **AC-006** | No secret leakage | 1. Run secret scan across repo: `! rg -i '(client_secret|password)\s*[:=]\s*["0-9a-zA-Z]{16,}'`.<br>2. Inspect Frappe `site_config.json`. | Zero secrets tracked in git. Yandex client secret is never injected into Frappe `site_config.json`. | PASS |
| 7 | **AC-007** | Existing RBAC intact | 1. Check user roles after SSO login.<br>2. Attempt to access DocType without assigned role. | User has assigned roles from `ELMS_SSO_DEFAULT_ROLES`. DocPerm check denies unauthorized access. UI visibility is not substitute for permissions. | PASS |

---

## Negative & Edge Case Verification

- **BN-001 (Missing secret in dev):** Provider omitted from site config; standard login form renders without 500 error.
- **BN-002 (Missing secret when required):** `SsoSettings` raises `ValueError` immediately upon initialization.
- **BN-003 (Empty Yandex credentials):** Keycloak entrypoint disables broker in `realm-elms.json`, local fallback authentication remains functional.
- **BN-004 (Forbidden direct Yandex route):** Bounded `rg` scan returns 0 hits for `custom/yandex` or `yandex_login`.
- **BN-005 (Internal container URL rejected):** `KEYCLOAK_PUBLIC_URL=http://keycloak:8080` is rejected by Pydantic validator.
- **BN-009 (Outage behavior):** When Yandex is unreachable, fallback local Keycloak credentials authenticate without phantom passwords.
- **BN-010 (CSS asset cache):** Clearing cache via `bench clear-cache` guarantees latest `login.css` is served.
