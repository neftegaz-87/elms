# Bugfix: SSO Keycloak Yandex Suite Alignment & Checklist Verification

- **Epic ID:** T-B03-elms-sso-keycloak-yandex
- **Role:** back
- **Date:** 2026-10-29
- **Source QA:** `memory-bank/back/qa/T-B03-elms-sso-keycloak-yandex/qa-20261029-sso.yaml`
- **Queue:** `memory-bank/back/bugfix/T-B03-elms-sso-keycloak-yandex/bugfix-queue.yaml`
- **Status:** PASS — BF-010 and BF-011 closed with targeted tests, full suite, real create-site, and live HTTP evidence

---

## 1. QA Root Cause Analysis
During BACK QA verification of epic `T-B03-elms-sso-keycloak-yandex`, defect items were identified:
- **BF-001 (suite_red):** `bin/pytest` did not forward CLI arguments (`$@`), preventing execution of `bin/pytest -q --tb=line`.
- **BF-002 (ac_gap):** Missing broker-login contract coverage for JIT provisioning (AC-6); the external Yandex browser journey was not available.
- **BF-003 (ac_gap):** Missing local-fallback contract coverage during a Yandex outage (AC-7); the external outage journey was not available.
- **BF-004 (suite_red):** Contradictory full-suite results (checks: 40 passed vs suite: 13 unit tests) across QA artifact.
- **BF-005 (ac_gap):** AC+8 evidence was status-only; manual setup checklist, outage branches, and port mapping lacked concrete outcomes and curl validation.
- **BF-006 (ac_gap):** Tracked `docker/keycloak/realm-elms.json` contained default plaintext passwords (`:admin`, `:fallback123`) in fallback interpolation syntax.
- **BF-007 (ac_gap):** `elms/elms/sso/ensure.py` checked credentials truthiness before `.strip()`, allowing whitespace-only strings to enable the Social Login Key.
- **BF-008 (ac_gap):** Missing live browser/API production path evidence for Keycloak OAuth redirect and broker endpoint (AC+2).
- **BF-009 (suite_red):** Conflicting suite count (40 in test_audit, 44 in full-suite result).
- **BF-010 (live_smoke):** The previous trace claimed a live AC+2 pass without a running
  Frappe/Keycloak stack or a captured HTTP response. It contained synthetic `mock_*`
  authorization data, so it could not serve as production-path evidence.
- **BF-011 (container_bootstrap):** ELMS declared the reserved Frappe `Core` module,
  which made site installation resolve DocTypes through the wrong Python namespace;
  installation also used an obsolete SMTP authentication method (`LOGIN`).

---

## 2. Changes Implemented (AC+)
- `bin/pytest`: Updated runner script to forward CLI arguments (`$@`), export `PYTHONPATH`, and execute pytest cleanly with `-o testpaths=elms/elms/tests --ignore=frappe` (BF-001).
- `elms/elms/tests/test_sso.py`: Added `simulate_keycloak_broker_login` helper and 4 automated test cases verifying JIT user creation/linking, immutable `sub` mapping, role assignment (`Desk User`, `ELMS LMS User`), and fail-closed checks on unverified email or missing `sub` (BF-002).
- `elms/elms/tests/test_sso.py`: Added `simulate_keycloak_auth_flow` helper and 4 automated test cases covering local Keycloak fallback login during Yandex external IdP outage, fail-closed handling on unreachable Yandex, existing account preservation, and fallback user realm alignment (BF-003).
- `memory-bank/back/qa/T-B03-elms-sso-keycloak-yandex/qa-20261029-sso.yaml`: Reconciled the historical full-suite execution command and evidence to one result (`44 passed` at that QA epoch) (BF-004).
- `docs/sso.md`: Documented concrete checklist outcomes for all verification branches (JIT login, fail-closed on Yandex outage without local creds, fallback with local Keycloak creds), detailed host/container port mappings (8082->8080->8000, 8480->8080), and added curl validation commands (BF-005).
- `docker/README.md`: Documented concrete checklist outcomes, host/container port mappings, and curl validation commands (BF-005).
- `docker/keycloak/realm-elms.json`: Removed default plaintext passwords (`:admin`, `:fallback123`); credentials now reference environment variables directly (`${env.KEYCLOAK_ADMIN_PASSWORD}`, `${env.KEYCLOAK_FALLBACK_PASSWORD}`) (BF-006).
- `elms/elms/sso/ensure.py`: Cleaned and stripped `client_id` and `client_secret` before validating non-empty status so whitespace-only inputs do not enable Social Login Key (BF-007).
- `docs/reports/sso-browser-api-trace.json`: Replaced the fabricated BF-008 trace with an explicit blocked artifact; it no longer claims that the browser/API journey was live.
- `elms/elms/tests/test_sso.py`: Added `simulate_frappe_oauth_redirect` and 4 automated test cases verifying AC+2 contract, OIDC 302 redirect generation, direct Yandex fail-closed behavior, and realm broker configuration (BF-008).
- `memory-bank/back/qa/T-B03-elms-sso-keycloak-yandex/qa-20261029-sso.yaml`: Reconciled test_audit suite count from 40 to 44 to match verified full suite result (BF-009).
- `memory-bank/back/bugfix/T-B03-elms-sso-keycloak-yandex/bugfix-queue.yaml`: Preserved BF-001 through BF-009 as historical `done` items and kept BF-010 open until the runtime command writes fresh evidence.
- `scripts/live_smoke.sh`: Added a black-box curl smoke that checks the live Keycloak
  discovery document, Frappe's real 302 redirect, and the Keycloak Yandex broker route;
  it writes raw response headers/bodies and refuses synthetic authorization data.
- `docs/reports/sso-browser-api-trace.json`: Replaced the fabricated trace with an
  explicit blocked artifact until the smoke has actually run.
- `elms/elms/tests/test_sso.py`: Added a regression guard that a trace cannot claim live
  pass without runtime HTTP evidence, command, timestamp, raw responses, and no `mock_*`.
- `elms/elms/modules.txt` and `elms/elms/elms_core/`: Renamed the ELMS module from the
  reserved `Core` namespace to `ELMS Core` and moved the DocType into the namespaced
  package, so Frappe's own `Core` remains resolvable during installation (BF-011).
- `elms/elms/install.py`: Changed the SMTP authentication method from `LOGIN` to the
  Frappe-supported `Basic` value and preserved fail-closed installation behavior (BF-011).
- `elms/elms/tests/test_sso.py` and `elms/elms/tests/test_roles_rbac.py`: Added guards
  for the module namespace, installation contract, and SSO runtime evidence (BF-011).

---

## 3. Non-Goals / Fallback Purge (AC−)
- No committed plaintext `client_secret` values or passwords in git tracking.
- No direct Yandex callback endpoint or second OAuth implementation module in Frappe (only `login_via_keycloak`).
- No fallback logic that silently swallows outage or missing credentials without fail-closed error.
- Unrelated modules and tests remain untouched.

---

## 4. Integration Rule Counterparts (§0.11)
- `docs/sso.md` and `docker/README.md` reflect verified container port mapping and curl endpoints.
- `elms/elms/tests/test_sso.py` covers both JIT broker flow, outage fallback branches, and AC+2 redirect/broker validation.
- Clean boundaries: zero orphan external references or phantom endpoints.

---

## 5. Historical blockers resolved
- **BF-001:** `suite_red: suite not full — record bin/pytest -q --tb=line` — PASS
- **BF-002:** `ac_gap: AC-6 — broker login contract coverage` — PASS (unit contract scenarios; no external Yandex login claimed)
- **BF-003:** `ac_gap: AC-7 — local fallback contract coverage` — PASS (unit outage scenarios; no external Yandex login claimed)
- **BF-004:** `suite_red: contradictory full-suite results` — PASS
- **BF-005:** `ac_gap: AC+8 evidence is status-only` — PASS
- **BF-006:** `ac_gap: AC+3 — tracked realm contains default plaintext passwords` — PASS
- **BF-007:** `ac_gap: AC+4 — whitespace-only credentials enable SSO` — PASS
- **BF-008:** `ac_gap: AC+2 — live browser/API evidence for Keycloak OAuth redirect and broker endpoint` — PASS
- **BF-009:** `suite_red: conflicting suite count (40 in test_audit, 44 in full-suite result)` — PASS
- **BF-010:** `live_smoke: real Frappe → Keycloak HTTP evidence is missing` — PASS
- **BF-011:** `container_bootstrap: ELMS Core module shadows Frappe Core during site creation` — PASS

The interactive Yandex step remains explicitly `not_run` because real Yandex
credentials and a registered callback were not supplied. The smoke proves the
configured Keycloak broker route is reachable and fails closed on a callback without
state; it does not claim a third-party login that was not executed.

---

## 6. Verification
- Verification command:
  ```bash
  bin/pytest -q --tb=line
  ```
  Result: `51 passed in 0.13s` (exit code 0).

- Targeted BF-011 command:
  ```bash
  bin/pytest -q --tb=line elms/elms/tests/test_sso.py elms/elms/tests/test_roles_rbac.py
  ```
  Result: `39 passed in 0.13s` (exit code 0).

- Real container bootstrap:
  `docker compose -f docker/compose.dev.yaml ps -a create-site` reported `Exited (0)`.
  `docker compose -f docker/compose.dev.yaml exec -T backend bench --site elms.localhost list-apps`
  reported `frappe 15.123.1` and `elms 0.0.1`.

Live verification command:

```bash
EVIDENCE_FILE=docs/reports/sso-browser-api-trace.json \
LIVE_SMOKE_COMMAND='timeout -k 10s 300s bash scripts/live_smoke.sh' \
timeout -k 10s 300s bash scripts/live_smoke.sh
```

Result at `2026-10-29T15:36:41Z`: exit code `0`. The evidence file records
`status: pass`, `live_evidence: true`, `exit_code: 0`, raw HTTP headers/bodies, and
real OAuth state/callback values. Observed responses were Keycloak discovery `200`,
Frappe `/login` `200`, Keycloak authorization `200`, and the Yandex broker endpoint
`502` with `Missing state parameter in response from identity provider`; the latter is
the expected fail-closed result when no real Yandex callback is submitted. The
interactive Yandex journey is `not_run`, not fabricated.
