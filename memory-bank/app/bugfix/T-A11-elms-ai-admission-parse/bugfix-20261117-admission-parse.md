# BUGFIX — T-A11-elms-ai-admission-parse

## BF-001 — admission parse provider and wire probe repaired

- Class: `product_bugfix`
- Surface: authenticated browser/wire journey (admission import)
- Root cause: the authenticated browser journey had no deterministic in-scope LLM provider configuration, and the first probe repair exposed a harness-only invalid-input mistake where the blank fixture was accepted as a zero-row import.
- Runtime cycles: two accepted `runtime-bootstrap` cycles are exhausted. Fresh evidence reclassified the blocker from auth/page access to the provider/configuration path; do not spawn another `runtime-bootstrap`.
- Exact VERIFY: `NEFTEGAZ_BROWSER=chromium timeout -k 10s 300s .venv/bin/python scripts/run_browser_qa.py`
- Evidence: [browser-evidence.json](/home/aero/PyProject/NEFTEGAZ/elms/browser-artifacts/browser-evidence.json)
- Evidence timestamp: `2026-11-18T00:39:07Z`
- Result: the non-smoke run authenticated Company Admin, configured the deterministic provider, rejected an invalid row explicitly, parsed a valid row, exported with HTTP 200, audited one-time reveal with HTTP 200 and invite token, and recorded no browser console or request failures.

The browser QA harness now starts a deterministic local test provider and builds an in-memory invalid-row fixture from the canonical valid workbook, so the wire journey verifies both fail-closed errors and the successful parse/export/reveal path.

## BF-002 — non-smoke admission wire journey restored

- Class: `product_bugfix`
- Surface: non-smoke authenticated browser/wire journey
- Root cause: `scripts/run_browser_qa.py` started and ran the admission journey only when `smoke_only` was enabled, so the required non-smoke wire command stopped after login checks.
- Exact VERIFY: `NEFTEGAZ_BROWSER=chromium timeout -k 10s 300s .venv/bin/python scripts/run_browser_qa.py`
- Evidence: [browser-evidence.json](/home/aero/PyProject/NEFTEGAZ/elms/browser-artifacts/browser-evidence.json)
- Evidence timestamp: `2026-11-18T00:39:07Z`
- Result: the non-smoke run authenticated Company Admin, configured the deterministic provider, rejected an invalid row explicitly, parsed a valid row, exported with HTTP 200, audited one-time reveal with HTTP 200 and invite token, and recorded no browser console or request failures.

The harness now starts the deterministic provider and executes the existing admission feature journey for the non-smoke entrypoint as well as smoke mode. Its typed evidence records the exact declared non-smoke VERIFY command.

## BF-003 — live HTTP smoke evidence persistence repaired

- Class: `product_bugfix`
- Surface: declared live HTTP smoke acceptance lane
- Root cause: `scripts/live_smoke.sh` emitted passing `sso-browser-api-trace/v1` evidence only to stdout when `EVIDENCE_FILE` was unset, so the exact queue VERIFY had no persisted typed `evidence_file` for the boundary.
- Exact VERIFY: `timeout -k 10s 300s bash scripts/live_smoke.sh`
- Evidence: [qa-20261118-admission-live-smoke.json](/home/aero/PyProject/NEFTEGAZ/elms/browser-artifacts/qa-20261118-admission-live-smoke.json)
- Evidence timestamp: `2026-11-18T07:18:16Z`
- Result: exit 0; fresh typed `sso-browser-api-trace/v1` evidence persisted by default with `status: pass`, `live_evidence: true`, and `exit_code: 0` for Keycloak discovery, Frappe login, SSO authorization, and organization access checks.

The live smoke entrypoint now defaults `EVIDENCE_FILE` to `browser-artifacts/qa-20261118-admission-live-smoke.json`; callers may still override it explicitly.

## BF-004 — obsolete live-smoke acceptance duplicate cancelled

- Class: `product_bugfix`
- Status: `cancelled`
- Result: obsolete duplicate of the live-smoke acceptance blocker; the absorbed `live_smoke: n/a` boundary behavior made this item a false positive.

## BF-005 — live HTTP smoke acceptance repaired

- Class: `product_bugfix`
- Surface: declared live HTTP smoke acceptance lane
- Root cause: the QA boundary had rejected the previous claimed live-smoke PASS because the declared acceptance path did not yield accepted typed evidence for the queue’s `evidence_file`.
- Exact VERIFY: `timeout -k 10s 300s bash scripts/live_smoke.sh`
- Evidence: [qa-20261118-admission-live-smoke.json](/home/aero/PyProject/NEFTEGAZ/elms/browser-artifacts/qa-20261118-admission-live-smoke.json)
- Evidence timestamp: `2026-11-18T07:18:16Z`
- Result: exit 0; typed `sso-browser-api-trace/v1` evidence has `status: pass`, `live_evidence: true`, and `exit_code: 0` for Keycloak discovery, Frappe login, SSO authorization, and organization access checks.

The live-smoke acceptance path now persists the fresh typed capture used by the exact queue VERIFY, closing BF-005 without another runtime-bootstrap cycle.

## BF-006 — live HTTP smoke acceptance reverified

- Class: `product_bugfix`
- Surface: declared live HTTP smoke acceptance lane
- Root cause: the source path was already repaired; the remaining open item held a stale boundary-rejected acceptance state and required a fresh typed capture from the exact queue VERIFY.
- Exact VERIFY: `timeout -k 10s 300s bash scripts/live_smoke.sh`
- Evidence: [qa-20261118-admission-live-smoke.json](/home/aero/PyProject/NEFTEGAZ/elms/browser-artifacts/qa-20261118-admission-live-smoke.json)
- Evidence timestamp: `2026-11-18T07:18:16Z`
- Result: exit 0; fresh `sso-browser-api-trace/v1` evidence records `status: pass`, `live_evidence: true`, and `exit_code: 0` for Keycloak discovery, Frappe login, SSO authorization, and organization access checks.
