## Epic

### Outcome
Каждый ELMS release связан с commit и immutable image digests, проходит existing tests/browser gates, protected approval, smoke и reversible pair rollback.

### In
GitHub Actions, GHCR, release manifest, allowlisted SSH wrapper, Vault/backup/capacity preflight and dev-target guard.

### Out
Build on production host, mutable tags, arbitrary SSH, automatic public edge switch and secret values in CI.

### Done when
Failed health/policy gate leaves previous release available and rollback restores backend/frontend/application pair as one release.
