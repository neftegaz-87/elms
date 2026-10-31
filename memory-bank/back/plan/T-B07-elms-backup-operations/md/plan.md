# [T-B07-elms-backup-operations] PLAN

**Дата:** 2026-10-31  
**Режим:** BACK/DEVOPS PLAN  
**Уровень:** L3  
**Статус:** active  
**Перенос:** адаптировано из `T-NF-007-backup-operations` для ELMS.

## Scope

Backup state classes: `sites`, `logs`, MariaDB `db-data`, Keycloak PostgreSQL `keycloak-db-data`, Redis queue data, Vault Raft data/snapshot и Caddy `caddy-data`/`caddy-config`. Review service state не дублируется: его backup contract принадлежит его репозиторию; ELMS сохраняет только handoff/config contract.

## Requirements

- **FR-001:** encrypted client-side off-host repository (restic/S3-compatible) with state manifest.
- **FR-002:** last-success age ≤24h, upload/checksum verification and retention.
- **FR-003:** restore-preflight rejects active production volumes and requires disposable target.
- **FR-004:** capacity hard block at configured threshold; no prune/delete/volume removal.
- **FR-005:** logs/manifests redact PII, OAuth and Vault recovery material.

## Gates

Production activation remains blocked until external repository, credentials, operations owner and target capacity are provided. The runner may use a disposable local fixture in CI.

## Implementation slices

1. State inventory, policy and non-secret manifest.
2. Encrypted backup/verify runner and capacity/read-only audit.
3. Disposable restore rehearsal with MariaDB/Keycloak/Vault smoke.

## Verification

```bash
python3 scripts/infra/backup_runner.py manifest --output /tmp/elms-backup-manifest.json
python3 scripts/infra/backup_runner.py restore-preflight --target /tmp/elms-disposable-restore
```

## ELMS implementation status

Implemented in this repository: non-secret state/restore-method manifest,
capacity gate, encrypted restic backup/verify commands, freshness report,
disposable restore-target protection, and systemd service/timer templates.
External repository credentials, consistent volume/database export wiring, and
the measured restore rehearsal require the production operations owner.

No production data is touched by these checks.
