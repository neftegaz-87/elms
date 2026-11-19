# BUGFIX T-A12 — B2B batch quotas

status: done
item: BF-T-A12-001
evidence_timestamp: 2026-11-18T21:44:05Z
evidence_file: memory-bank/app/qa/T-A12-elms-b2b-batch-quotas/evidence-20261118-wire.json

## Result

`check-bugfix-queue` → `bugfix_queue_ready`.  
`verify-bugfix` PASS accepted → cursor advanced **BUGFIX → QA**.

Wire green (refreshed): `JRN-A11-ADMISSION-IMPORT` + `JRN-T-A12-B2B-CONFIRM-001` pass;  
`confirm_admission_import` → `ok=true`, `status=confirmed`, `enrolled_count=1`.  
Targeted pytest: 15 passed.

## Changes Implemented (AC+)

1. `parse_admission_request` strips Frappe transport keys (`cmd`, `csrf_token`) before pydantic forbid.
2. Platform-owner org flags `can_publish_own` / `can_use_owner_catalog` (tenant + wire bootstrap).
3. B2B profile upsert → `ELMS Admission Profile` with `flags.from_b2b_admission`.
4. Enrollment writes `user` + `organization` + `source_import` + learner snapshot fields.
5. Audit uses `activity_type` + `timestamp`; savepoint rollback uses `save_point=`.
6. Harness clears stale preview/result before T-A12 clicks; login readiness without restart thrash.
7. Project rules: one `make local.restart` per QA phase; diagnose prefers last emitted evidence.

## AC−

- Do not weaken wire/browser gates or absorb T-A12 into smoke-only.
- Do not promote historical `qa-20261118-b2b-batch-quotas-reqa.yaml` (verdict fail) to PASS.
- Do not restart before every browser retry.

## Verification

- `./bin/pytest -q elms/elms/tests/test_b2b_batch_quotas.py` → 15 passed
- `NEFTEGAZ_BROWSER=chromium timeout -k 10s 300s .venv/bin/python scripts/run_browser_qa.py` → PASSED exit 0
- `loop.py check-bugfix-queue` → ok / `bugfix_queue_ready`
- `verify-bugfix` PASS → phase QA

## Re-QA note

Next `APP QA` must write a **new** `qa-*.yaml` from a fresh charter.  
Historical fail baseline stays fail (`historical_baseline: true`). Use current wire evidence path above; keep required lanes backend + frontend_build + wire_journey.
