# BUGFIX — T-A14 admin organization view

## BF-001

- Status: done
- Class: harness_probe
- Root cause: T-A14 typed checks pass, but expected platform mutation denial tracebacks had no method name in console text and were classified as unexpected by the browser-runtime probe.
- Allowed write scope: `scripts/run_browser_qa.py`; `memory-bank/app/qa/T-A14-elms-admin-org-view-all/qa-20261119-admin-org-view-all-app-lanes.yaml`
- Targeted verification: `NEFTEGAZ_BROWSER=chromium timeout -k 10s 300s .venv/bin/python scripts/run_browser_qa.py`
- Latest evidence: `browser-artifacts/browser-evidence.json`, timestamp `2026-11-19T12:23:35Z`; VERIFY exit 0.
- Root cause confirmed: expected 403 calls emit server traceback console messages without method names, so the harness classifies them as unexpected. Fix-worker is active; preserve denial checks and fail on genuinely unexpected errors.

## Verification

- Queue verification is `pass`; BF-001 is terminal `done` at evidence timestamp `2026-11-19T12:23:35Z`.
- Runtime activation passed; no runtime-bootstrap cycle was warranted. The harness now classifies the expected denial tracebacks from the five expected 403 responses as expected console errors; unrelated T-A13 evidence remains non-blocking.

## Changes Implemented

- Changed file: `scripts/run_browser_qa.py`.
- Behavior: expected denial tracebacks from the five expected 403 responses are classified as expected console errors, while denial checks remain enforced and genuinely unexpected errors still fail the probe.
- Evidence: `browser-artifacts/browser-evidence.json`, timestamp `2026-11-19T12:23:35Z`; targeted verification exited 0.

## §0.11

- [x] `scripts/run_browser_qa.py` — counterpart: expected-denial console-error classification, with denial checks preserved and unexpected errors still failing; evidence: `browser-artifacts/browser-evidence.json` at `2026-11-19T12:23:35Z`, targeted verification exit 0.
- [x] `memory-bank/app/qa/T-A14-elms-admin-org-view-all/qa-20261119-admin-org-view-all-app-lanes.yaml` — counterpart: the QA app-lanes contract remains paired with the harness denial checks; evidence: queue verification is `pass`, BF-001 is terminal `done`, and the targeted verification exited 0.
