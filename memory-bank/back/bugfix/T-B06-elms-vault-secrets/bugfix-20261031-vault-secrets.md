# Bugfix: purge stale Keycloak fallback contracts

- **Epic ID:** T-B06-elms-vault-secrets
- **Role:** BACK
- **Source QA:** `memory-bank/back/qa/T-B06-elms-vault-secrets/qa-20261031-vault-secrets.yaml`
- **Queue:** `memory-bank/back/bugfix/T-B06-elms-vault-secrets/bugfix-queue.yaml`
- **Status:** PASS — BF-001 and BF-002 closed

## Root cause

The T-B06 implementation correctly removed the production `fallback.user` realm
entry and the local Keycloak outage path, but brownfield SSO tests and
`docs/sso.md` still described the deleted behavior. The full suite therefore
failed four stale assertions even though the Vault contract and negative
fixtures passed.

## Changes

- Updated the four stale SSO acceptance/configuration assertions to verify that
  the fallback realm user is purged while retaining broker and fail-closed
  coverage.
- Rewrote `docs/sso.md` so Keycloak remains the sole production identity
  boundary, Vault Agent is the production secret delivery path, and Yandex
  outages fail closed without a local fallback account.
- Kept credentials and secret values out of the documentation and tests.

Changed paths:

- `elms/elms/tests/test_login_ui.py`
- `elms/elms/tests/test_sso.py`
- `elms/elms/tests/test_sso_config.py`
- `docs/sso.md`

## Verification

```text
bin/pytest -q --tb=line
```

Result: `87 passed, 2 skipped` (exit code 0).

The bounded documentation scan for `fallback.user`, `local.*fallback`, and
`fallback.*local` returned no matches in `docs/sso.md`. The previously passing
infra contract suite and Vault redaction/recovery checks remain unchanged.

The interactive Yandex consent flow and real production Vault initialization
remain explicit operator gates; no synthetic success is claimed.
