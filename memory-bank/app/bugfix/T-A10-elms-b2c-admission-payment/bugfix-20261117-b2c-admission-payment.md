# BUGFIX — T-A10 B2C admission payment

## BF-001 — live admission Page missing

- Root cause: the standard `Page` JSON was present in source, but the live Frappe site had no `elms-admission` Page record. The existing `page_js` mapping could not help before the record was installed.
- Fix: `elms/elms/hooks.py` now imports the standard Page during both app install and migration when the record is absent.
- Targeted evidence: source/install wiring passed; seven admission UI assertions passed.
- Runtime check: after `bench --site all migrate` and backend/frontend restart, authenticated navigation reached the admission form and catalog.

## Follow-up discovered during the same wire journey

BF-001 verification advanced to profile and document upload, then exposed BF-002: `create_payment` queried optional `amount`/`price` fields that are not present on the live `ELMS Batch` or `ELMS Course` DocTypes. This is a concrete backend schema-gap blocker, queued as BF-002 with its own bounded write set.

## Queue state

- BF-001: done; source and runtime Page installation fixed.
- BF-002: done; optional pricing lookup is schema-aware and its focused regression test passes (5 passed).
- BF-003: done; the ELMS Core Payment DocType source/controller is restored and the focused payment/webhook tests pass (9 passed).
- BF-004: done; fresh fake provider instances now generate unique provider payment identifiers and the focused payment/webhook regression passes (10 passed).
- BF-005: done; the verified paid state is persisted before enrollment enforcement and the focused payment/webhook regression passes (11 passed).
- BF-006: done; the live Page installation wiring was verified by the complete authenticated admission/payment wire journey.
- Runtime follow-up: the first post-BF-003 wire run exposed duplicate `fake-payment-1`; the next wire run exposed webhook state ordering, both fixed in this session.
- Overall verification: pass; the 2026-11-17T11:31:42Z authenticated wire run passed login, live admission Page, private profile uploads, pending payment, signed paid webhook, and active enrollment.

## BF-006 — queue closure reconciliation

- The managed `bugfix-fix` worker confirmed the source Page definition and install/migration synchronization wiring without changing product files.
- Evidence: `memory-bank/app/qa/T-A10-elms-b2c-admission-payment/admission-wire-20261117.json` is a live pass at `2026-11-17T11:36:18Z`, covering login, admission Page, private profile upload, payment creation, signed paid webhook, and active enrollment.
- Queue anchors and `verification.last_run_at` use that exact evidence timestamp.

## BF-006 — managed worker closure update

- The managed `bugfix-fix` result for BF-006 was validated as `done`.
- Live evidence was refreshed at `2026-11-17T12:05:40.643476Z` with exit 0: login,
  admission Page, private profile upload, payment creation, signed paid webhook,
  and active enrollment all passed.
- Changed source path: `elms/elms/hooks.py`; the declared wire evidence file was
  refreshed at the same timestamp.
- The runtime evidence observation includes `browser-artifacts/admission-wire.png`;
  queue reconciliation now reports `bugfix_queue_ready`.

## BF-006 — final managed verification

- The managed `bugfix-fix` worker returned a validated `done` result for BF-006.
- Live evidence was refreshed at `2026-11-17T12:37:10.213605Z` with exit 0 and passed
  source Page wiring, authenticated login, admission Page, private profile upload,
  payment creation, signed paid webhook, and active enrollment.
- Queue anchors and `verification.last_run_at` use that exact evidence timestamp.
