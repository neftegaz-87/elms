# Bugfix: canonical live-smoke Keycloak host default

- **Epic ID:** T-B05-elms-production-container-stack
- **Role:** BACK
- **Source QA:** `memory-bank/back/qa/T-B05-elms-production-container-stack/qa-20261031-production-container-stack.yaml`
- **Queue:** `memory-bank/back/bugfix/T-B05-elms-production-container-stack/bugfix-queue.yaml`
- **Status:** PASS — BF-001 closed after targeted regression and canonical live HTTP smoke

## Root cause

The canonical `scripts/live_smoke.sh` run uses its no-override default
`KEYCLOAK_PUBLIC_URL=http://127.0.0.1:8480`. The running dev Compose/Frappe
contract publishes and advertises Keycloak as
`http://elms-keycloak.localhost:8480`, so the smoke compares the real Frappe
authorization link with the wrong expected endpoint and exits before the
authorization journey.

Evidence:

- `scripts/live_smoke.sh` default disagrees with `docker/.env.dev`.
- `timeout -k 10s 300s bash scripts/live_smoke.sh` exits 1 with
  `Frappe Keycloak link points to an unexpected authorization endpoint`.
- The same live HTTP journey passes when both public URL variables are
  explicitly set to `http://elms-keycloak.localhost:8480`.

## Changes Implemented (AC+)

BF-001 adds a focused regression assertion for the no-override dev default,
then aligns the script default with the canonical dev public hostname. Explicit
environment overrides remain supported.

Changed paths:

- `scripts/live_smoke.sh` — default `KEYCLOAK_PUBLIC_URL` now matches the dev
  public hostname.
- `tests/infra/test_live_smoke_contract.py` — regression assertion locks the
  no-override default to the dev contract.
- `docs/reports/elms-production-qa-default-live-smoke.json` — fresh typed live
  HTTP evidence from the canonical command.

## Acceptance negatives (AC−)

- No fallback or error suppression was added; explicit environment overrides
  remain authoritative and the smoke still fails closed on a mismatched
  authorization endpoint.
- No production secrets, Compose services, or public edge settings were
  changed.

## Integration counterparts (§0.11)

- The smoke's default is aligned with `docker/.env.dev`; the live evidence
  records the Frappe login, Keycloak authorization, and broker boundaries in
  one typed artifact.
- The regression remains isolated to the smoke contract and does not create a
  second OAuth implementation or service entrypoint.

## Verification

The regression test passed and the canonical no-override live smoke passed against
the running Docker stack. The typed runtime artifact was refreshed at
`2026-10-31T14:04:30Z`.

```text
python3 -m pytest -q tests/infra/test_live_smoke_contract.py && LIVE_SMOKE_COMMAND='timeout -k 10s 300s bash scripts/live_smoke.sh' EVIDENCE_FILE=docs/reports/elms-production-qa-default-live-smoke.json timeout -k 10s 300s bash scripts/live_smoke.sh
```

Result: `1 passed`; live smoke exit `0`; evidence is
`docs/reports/elms-production-qa-default-live-smoke.json` with
`status: pass`, `live_evidence: true`, and the observed Frappe/Keycloak/broker
journeys.
