# Bugfix: ELMS Keycloak Login UI Styling & Spec Override

- **Epic ID:** T-A01-elms-keycloak-login-ui
- **Role:** app
- **Date:** 2026-10-29
- **Source QA:** `memory-bank/app/qa/T-A01-elms-keycloak-login-ui/qa-20261029-login-ui.yaml`
- **Queue:** `memory-bank/app/bugfix/T-A01-elms-keycloak-login-ui/bugfix-queue.yaml`
- **Status:** PASS — BF-001 closed with elevated selector specificity, `!important` token rules, updated unit test assertions, and live Playwright browser evidence

---

## 1. QA Root Cause Analysis
During APP QA verification of epic `T-A01-elms-keycloak-login-ui`, defect `BF-001` was identified:
- **BF-001 (lane:browser):** `.btn-keycloak background-color` was overridden by Frappe core `login.bundle.css` to `var(--gray-100)` (`rgb(243, 243, 243)`). Frappe's `head_include` injects `login.bundle.css` after `web_include_css` from `head.html`, causing equal-specificity declarations (`.btn-login-option.btn-keycloak`) to resolve to the light gray style instead of the Neftegaz cobalt action token (`#0d4cd3`). This produced a low-contrast, non-compliant button.

---

## 2. Changes Implemented (AC+)
- `elms/elms/public/css/login.css`:
  - Elevated selector specificity for `.for-login .page-card .page-card-body .btn-login-option.btn-keycloak`, `.social-logins`, and related link selectors.
  - Added `!important` to `background`, `background-color`, `border`, `color`, `border-radius`, and control height/min-height properties to prevent later stylesheet overrides.
  - Added `!important` to hover, focus-visible, and active pseudo-class states (`background-color: var(--elms-login-action-hover, #0a3fb0) !important`).
- `elms/elms/tests/test_login_ui.py`:
  - Updated `test_login_css_neftegaz_design_tokens` to explicitly check that `!important` is enforced on `.btn-keycloak` background, height, and border-radius rules.

---

## 3. Non-Goals / Fallback Purge (AC−)
- No modification of upstream Frappe `login.bundle.css` or template forks.
- No direct Yandex login button introduced.
- No regression in accessibility or reduced-motion media queries.

---

## 4. Integration Rule Counterparts (§0.11)
- Keycloak SSO button retains single authoritative action styling matching Neftegaz design token `#0d4cd3`.
- Tested in real headless browser against live container `http://elms.localhost:8082`.

---

## 5. Blockers Resolved
- **BF-001:** `lane:browser: .btn-keycloak background color overridden by login.bundle.css` — PASS
  - Verified background color: `rgb(13, 76, 211)`
  - Verified dimensions: height `44px`, border-radius `3px`
  - Unit test suite: `6 passed`
  - Browser QA suite: all checks passed (`passed: true`)

---

## 6. Verification
- Targeted unit tests:
  ```bash
  PYTHONPATH=elms python3 elms/elms/tests/test_login_ui.py
  ```
  Result: `Ran 6 tests in 0.001s: OK`.

- Live browser QA:
  ```bash
  python3 scripts/run_browser_qa.py
  ```
  Result:
  ```json
  {
    "schema": "browser-qa-trace/v1",
    "base_url": "http://elms.localhost:8082",
    "passed": true,
    "computed_style": {
      "height": "44px",
      "borderRadius": "3px",
      "backgroundColor": "rgb(13, 76, 211)",
      "color": "rgb(255, 255, 255)",
      "display": "inline-flex",
      "minHeight": "44px"
    }
  }
  ```
  Status: `Browser QA PASSED`.

---

## 7. Resolution of BF-002: Yandex Broker Flow Validation (AC+4)
- **Defect:** `ac_gap: AC+4 Yandex broker flow through Keycloak broker without direct Frappe call`
- **Root Cause:** Live smoke script previously checked the broker endpoint status code without validating the internal broker routing, social provider entrypoint on the Keycloak authentication page, and absence of direct Yandex routes in Frappe login response, leaving the broker evidence open to misinterpretation when external Yandex interactive consent is skipped in test environments.
- **Fix:**
  - Updated `scripts/live_smoke.sh` to explicitly assert the Keycloak login page serves the Yandex broker link (`/realms/elms/broker/yandex/login`), the Keycloak endpoint is handled by `IdentityBrokerService`, and the Frappe login page contains zero direct Yandex login routes or buttons.
  - Executed `EVIDENCE_FILE=docs/reports/sso-browser-api-trace.json bash scripts/live_smoke.sh` to generate complete runtime HTTP trace evidence confirming `status: "pass"`, `live_evidence: true`, and `exit_code: 0`.
- **Verification:**
  - `bash scripts/live_smoke.sh`: exit 0, status pass.
  - `bin/pytest`: 65 passed in 0.28s.
  - `python3 scripts/run_browser_qa.py`: pass (login button styled with cobalt action `#0d4cd3`, height 44px, border-radius 3px).
