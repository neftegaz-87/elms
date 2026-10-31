# [T-B08-elms-cicd-release-rollback] PLAN

**Дата:** 2026-10-31  
**Режим:** BACK/DEVOPS PLAN  
**Уровень:** L3  
**Статус:** active  
**Перенос:** адаптировано из `T-NF-008-cicd-release-rollback` для ELMS.

## Dependencies

`T-B05` image/compose contract, `T-B06` Vault preflight, `T-B07` backup/capacity gate. Без отдельного dev target workflow остаётся build/verify-only.

## Requirements

- **FR-001:** existing Frappe/app tests, browser QA and compose policy precede GHCR push.
- **FR-002:** backend image is built from repo and tagged by commit SHA; deploy uses digest, not `latest`.
- **FR-003:** release manifest contains commit, image refs/digests, compose hash and smoke metadata, no secrets.
- **FR-004:** production uses GitHub Environment approval and an allowlisted remote wrapper with lock/preflight.
- **FR-005:** rollback restores previous verified image/config pair and never deletes state volumes.
- **FR-006:** any remote target must be explicit, pinned by known-hosts, and
  different from production; this repository does not default a dev deploy to
  the production host.

## Implementation slices

1. Manifest validator and workflow build/push metadata.
2. Server-side `deploy_wrapper.py` deploy/status/rollback allowlist.
3. Forced-health-failure rollback fixture and redaction checks.

## Verification

```bash
python3 scripts/infra/check_release_manifest.py --fixture tests/infra/fixtures/release-manifest.json
python3 scripts/infra/deploy_wrapper.py --help
```

## ELMS implementation status

Implemented in this repository: protected GitHub workflow, GHCR commit-tagged
image builds, digest release manifest, contract/app test gates, SSH known-host
handoff, serialized server wrapper, Vault/backup evidence gates, digest
override into Compose, health/internal smoke, and volume-preserving release
recording. Real registry credentials, protected Environment approval, server
evidence, and a disposable forced-failure rollback remain deployment gates.

The workflow never receives or prints Vault application values.
