# [T-B06-elms-vault-secrets] PLAN

**Дата:** 2026-10-31  
**Режим:** BACK/DEVOPS PLAN  
**Уровень:** L3  
**Статус:** active  
**Перенос:** адаптировано из `T-NF-006-local-vault-secrets` для ELMS.

## Context and boundary

ELMS использует MariaDB, Keycloak PostgreSQL, Redis и Frappe site volumes. Vault хранит static runtime credentials: DB roots, Frappe admin/bootstrap, Keycloak admin/client/DB, Yandex broker и review handoff secret. Пользовательские OAuth/session state остаются application-owned. `ELMS_REVIEW_HANDOFF_SECRET` должен совпадать с first-party review service, но значение не копируется в git.

## Technology axiom

Vault KV v2 plus authenticated Vault Agent render is the sole production static-secret
source of truth. Production has no direct environment, root-token, local-secret, or dev
fallback; application-owned OAuth/session state remains writable and is never placed on a
read-only Vault path.

## Replacement / sunset

### Replacement / sunset A

| Legacy surface | Replacement | Sunset/control |
|---|---|---|
| Direct production DB/Frappe/Keycloak/Yandex/review credentials in environment, images, or manifests | Authenticated Vault Agent rendered files and supported `*_PASSWORD_FILE` delivery | Delete direct credential interpolation and reject secret-bearing image/manifest artifacts |
| Secret-value logging in infra helpers | Redacted status-only diagnostics | Delete value-printing paths and grep stdout/stderr controls |
| Obsolete direct-secret or fallback tests | Synthetic fail-closed Vault and disposable restore fixtures | Rewrite or delete old-contract tests |

### Replacement / sunset B

| Legacy surface | Replacement | Sunset/control |
|---|---|---|
| Vault dev mode and public `8200` entrypoint | Pinned integrated-Raft Vault on a private Compose-only listener | Delete dev configuration and host port publication |

### Replacement / sunset C

| Legacy surface | Replacement | Sunset/control |
|---|---|---|
| Root-token runtime injection | Least-privilege authenticated AppRole/Vault Agent render | Delete root-token runtime paths |
| Local-secret, `.env`/dev, or synthetic fallback during production startup | Non-zero preflight and fail-closed promotion gate | Delete fallback callers and require complete render |
| Read-only Vault storage for OAuth/session state | Writable application-owned OAuth/session state | Keep user state outside the read-only secret-render boundary |

### Replacement / sunset I

| Legacy surface | Replacement | Sunset/control |
|---|---|---|
| Production secret-copy, paste, or custody instructions | Non-secret Vault/AppRole operator runbooks | Rewrite instructions so values are never copied, printed, or committed |
| Secret-bearing image, log, or release-manifest instructions/artifacts | Redacted build/release evidence | Purge values from images, logs, and manifests |

## Dependencies

- `T-B05` — production service/network/volume boundary.
- `T-B07` consumes Vault Raft snapshot.
- `T-B08` uses Vault preflight; GitHub не получает application secret values.

## Requirements

- **FR-001:** pinned Vault image, Raft volume, no host port and no dev mode.
- **FR-002:** KV v2 paths/policies are least-privilege; backend/Keycloak receive only their contract.
- **FR-003:** Agent renders protected env/file volume; MariaDB/PostgreSQL use `*_PASSWORD_FILE` where supported.
- **FR-004:** sealed/unavailable/unauthorized/missing key → non-zero preflight and no application promotion.
- **FR-005:** local/dev synthetic secrets remain independent.
- **FR-006:** init/unseal/rotation/snapshot/restore/revoke runbooks never print values.

## Open gates

- Human custodian and offline location for unseal/recovery material must be named before real production bootstrap.
- AppRole role/secret-id files are root-owned outside repository.

## Implementation slices

1. Vault config, compose service, protected render volume and non-secret templates.
2. AppRole/Agent startup gate for MariaDB, Keycloak DB, Frappe and Keycloak.
3. Synthetic negative tests: sealed, missing path, unauthorized, redaction and restore.

## Verification

```bash
bash scripts/infra/vault_preflight.sh --env-file docker/.env.prod --dry-run
python3 scripts/infra/check_secret_contract.py --compose docker/compose.prod.yaml
bash scripts/infra/vault_bootstrap.sh --help
bash scripts/infra/vault_snapshot.sh --help
```

## ELMS implementation status

Implemented in this repository: single-node Raft config, KV v2 runtime
templates, read-only `elms-agent` policy, AppRole bootstrap helper,
root-owned role/secret-id contract, protected render volume, password-file
delivery for MariaDB/PostgreSQL, and fail-closed application entrypoints.
Initialization/unseal, recovery custody, real KV values, and rotation remain
explicit operator gates; no production secret is committed or run by CI.

Real secret initialization is an operator action; it is not run by CI or this change.
