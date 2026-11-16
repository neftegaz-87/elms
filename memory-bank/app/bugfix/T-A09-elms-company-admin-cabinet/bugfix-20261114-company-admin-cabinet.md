# APP BUGFIX — T-A09 elms company admin cabinet

## BF-T-A09-001 — done

- Status: `done`
- Root cause: active Keycloak/runtime authentication was intermittent; the earlier cabinet lane stopped before the authenticated journey with the documented runtime-auth blocker.
- Regression red: the pre-fix runtime capture could not start the authenticated cabinet journey.
- Fix: restored a healthy active authenticated admin runtime and captured the journey again. No product-code, login-path, queue, or activeContext changes were required.
- Targeted green: the fresh evidence is `status=pass`; login, cabinet route, empty organization roster, server-side export, UTF-8 CSV, and no-DOM-only-CSV checks all pass.
- Evidence file: `memory-bank/app/qa/T-A09-elms-company-admin-cabinet/browser-wire-20261114.json`
- Evidence timestamp: `2026-11-14T09:33:14.076959Z`
- Changed paths: this bugfix artifact only.

## BF-T-A09-002 — done

- Status: `done`
- Root cause: the authenticated Company Admin roster and server-side CSV wire journey had no fresh runtime capture, so the QA lane remained unverified.
- Regression red: before the fresh capture, the authenticated roster/export journey was unverified because the runtime authentication blocker stopped the wire journey.
- Fix: repeated `JRN-T-A09-CABINET-001` with an authenticated Administrator session and recorded the roster, empty state, server API responses, and UTF-8 CSV response.
- Evidence file: `memory-bank/app/qa/T-A09-elms-company-admin-cabinet/browser-wire-20261114.json`
- Evidence timestamp: `2026-11-14T09:33:14.076959Z`
- Targeted green: evidence status is `pass`; roster API returned HTTP 200 with the empty organization state, server-side CSV export returned HTTP 200 with UTF-8/BOM payload, and console errors are empty. The capture proves no DOM-only CSV workaround.
- Changed paths: this bugfix artifact only.
