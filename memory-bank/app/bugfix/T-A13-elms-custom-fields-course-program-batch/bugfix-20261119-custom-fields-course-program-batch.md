# BUGFIX — T-A13 custom fields for Course / Program / Batch

schema: app-bugfix/v1
epic_id: T-A13-elms-custom-fields-course-program-batch
role: app
status: done
queue: bugfix-queue.yaml

## Result

BF-001, BF-002, and BF-003 are closed. The browser harness captures the
authenticated T-A13 custom-fields journey: definition save, Course Additional
control render, and Course value save/readback through the canonical typed API.
Queue closure metadata and QA status match the typed browser artifact.

## Changes Implemented

- `scripts/run_browser_qa.py` now captures the typed T-A13 custom-fields journey:
  definition save/readback, Course Additional control rendering, and Course value
  save/readback through `frappe.desk.form.save.savedocs`.
- BUGFIX queue and QA closure metadata now use the browser artifact timestamp
  `2026-11-19T09:06:11Z` as their evidence anchor.

## AC-

- Out of scope disposition: unrelated admission journeys and product areas outside
  the T-A13 Course / Program / Batch custom-fields journey were not changed.

## §0.11 Counterpart Mapping

- `scripts/run_browser_qa.py` → `browser-artifacts/browser-evidence.json`: the
  browser journey implementation is mapped to its typed runtime evidence capture.

## Verification

- Command: `NEFTEGAZ_BROWSER=chromium timeout -k 10s 300s .venv/bin/python scripts/run_browser_qa.py`
- Status: pass (exit 0)
- Evidence: `browser-artifacts/browser-evidence.json`
- Evidence timestamp: `2026-11-19T09:06:11Z`
- Queue verification: `python3 /home/aero/PyProject/dev-hub/bin/loop.py check-bugfix-queue --project /home/aero/PyProject/NEFTEGAZ/elms --json` (exit 0)

## Item

| ID | Status | Root-cause paths | Evidence |
| --- | --- | --- | --- |
| BF-001 | done | `scripts/run_browser_qa.py`, `elms/elms/public/js/elms-custom-fields-page.js`, `elms/elms/public/js/custom-fields.js`, `elms/elms/lms/api/custom_fields.py` | T-A13 Course control render and value save/readback passed. |
| BF-002 | done | `scripts/run_browser_qa.py` | T-A13 Course value save/readback passed; canonical `frappe.desk.form.save.savedocs` returned HTTP 200 and matching readbacks. |
| BF-003 | done | `memory-bank/app/bugfix/T-A13-elms-custom-fields-course-program-batch/bugfix-queue.yaml`, `memory-bank/app/qa/T-A13-elms-custom-fields-course-program-batch/qa-20261119-custom-fields-qa.yaml` | Queue metadata, QA verdict, and closure anchors match the typed browser artifact at `2026-11-19T09:06:11Z`. |
