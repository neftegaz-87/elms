# ELMS production operations

This runbook is the operator boundary for the production Compose graph. It
does not contain application credentials, Vault recovery material, or commands
that print them.

The boundary is explicit: `docker/compose.prod.yaml` is the image-only
production source of truth. Checkout builds are allowed only through
`docker/compose.prod.build.yaml` for local/CI or the isolated staged rehearsal;
the public `docker/compose.prod.edge.yaml` overlay requires owner approval and
fresh predecessor evidence. `docker/.env.dev` remains a synthetic dev-only
environment and is never a source of production secrets or production URLs.

## Before bootstrap

The owner must name an operations custodian and an offline location for Vault
recovery material. Prepare a real `docker/.env.prod` containing only
hostnames, image references and the paths to root-owned AppRole files. The
review service remains a separate runtime; its handoff secret is written to
Vault at `elms/data/runtime`, never to this repository.

Validate the static contract first:

```bash
python scripts/infra/check_compose_policy.py
python scripts/infra/check_secret_contract.py
bash scripts/infra/vault_preflight.sh --env-file docker/.env.prod --dry-run
docker compose --env-file docker/.env.prod \
  -f docker/compose.prod.yaml config --quiet
```

## Vault bootstrap

Start only the Vault service on an isolated maintenance project. Initialize it
once from the secure operator console, storing the protected recovery material
offline according to the organization's custody policy. Do not put the output
in CI logs, shell history, the repository, or a runtime container.

After Vault is initialized, run the fixed bootstrap helper with an
operator credential held in a protected operator environment. The helper
installs the read-only AppRole policy and writes only the role/secret ID files.

```bash
export ELMS_VAULT_OPERATOR_TOKEN
bash scripts/infra/vault_bootstrap.sh bootstrap --env-file docker/.env.prod
unset ELMS_VAULT_OPERATOR_TOKEN
```

The variable is injected by the approved secure operator session; its value is
never copied into this command, shell history, CI, or documentation. Revoke
the temporary operator credential after the policy write. Populate the KV v2
object using the approved secret-management procedure; required keys are
enforced by the Vault render contract.

Rotate or revoke an AppRole secret ID only from the same protected session:

```bash
export ELMS_VAULT_OPERATOR_TOKEN
bash scripts/infra/vault_bootstrap.sh rotate --env-file docker/.env.prod
bash scripts/infra/vault_bootstrap.sh revoke --env-file docker/.env.prod
unset ELMS_VAULT_OPERATOR_TOKEN
```

Then verify the authenticated render without printing any value:

```bash
bash scripts/infra/vault_preflight.sh --env-file docker/.env.prod
```

Missing, sealed, unauthorized, or partially rendered Vault state blocks all
application promotion.

Capture a Raft snapshot through the fixed helper and place it in the encrypted
off-host backup flow. The output path must be protected and must not be the
active Docker volume.

```bash
export ELMS_VAULT_OPERATOR_TOKEN
bash scripts/infra/vault_snapshot.sh snapshot \
  --env-file docker/.env.prod \
  --output /var/lib/elms-backup/vault/raft.snap
unset ELMS_VAULT_OPERATOR_TOKEN
```

Restore is accepted only into a disposable project named `elms-vault-restore-*`.
For local rehearsal, use the synthetic fixture path and inspect only its
redacted status marker; never restore into an active production volume.

```bash
rehearsal_dir="$(mktemp -d)"
python scripts/infra/backup_runner.py restore-preflight \
  --target "$rehearsal_dir/restore"
bash scripts/infra/vault_snapshot.sh snapshot \
  --fixture tests/infra/fixtures/vault-synthetic-snapshot.json \
  --output "$rehearsal_dir/raft.snap"
bash scripts/infra/vault_snapshot.sh restore --fixture \
  --input "$rehearsal_dir/raft.snap" \
  --target "$rehearsal_dir/restore"
```

## Staged release

Run the high-port rehearsal in a separate Compose project. It does not own
public ports and does not change DNS, firewall rules, or a host Caddy service.

```bash
bash scripts/infra/compose_smoke.sh \
  --profile staged --env-file docker/.env.prod --dry-run
```

For the live rehearsal, use a separately approved staged env/project and run
the same command without `--dry-run`. The script checks Frappe `/login` and
Keycloak discovery, then removes only that staged project unless `--keep` was
explicitly requested.

## Backup and restore gate

Generate a non-secret state manifest and perform the disposable-target
preflight before accepting a release. The external restic repository,
credentials, freshness evidence, and restore owner are deployment inputs.
The manifest is the contract for `sites`, `logs`, MariaDB `db-data`, Keycloak
PostgreSQL `keycloak-db-data`, Redis queue data, Vault Raft state, and Caddy
`caddy-data`/`caddy-config`. It declares client-side encryption, a hard
capacity gate, RPO 24h, RTO 4h, and 30-day retention; status output is
redacted and never contains PII, OAuth material, or Vault recovery values.

```bash
python scripts/infra/backup_runner.py manifest \
  --output /var/lib/elms-backup/elms-backup-manifest.json
python scripts/infra/backup_runner.py restore-preflight \
  --target /var/lib/elms-restore-rehearsal
```

The restore rehearsal is disposable-only and has a machine-checkable,
redacted handoff. Create the contract beside the rehearsal evidence, then
record owner evidence for each smoke check in this order; no live credentials
or application data are copied into the status file:

```bash
rehearsal_dir="$(mktemp -d)"
python scripts/infra/backup_runner.py restore-rehearsal-manifest \
  --output "$rehearsal_dir/restore-rehearsal.json"
python scripts/infra/backup_runner.py restore-preflight \
  --target "$rehearsal_dir/target"
```

The owner-approved rehearsal order is: (1) MariaDB `db-data` logical-dump
import and schema smoke, (2) Keycloak PostgreSQL logical-dump import and
identity-discovery smoke, (3) Vault Raft synthetic snapshot restore with only
a redacted marker, and (4) Caddy data/config configuration and persisted
edge-state smoke. The owner records status-only evidence and elapsed time
against the RTO 4h target. Review-service application state remains owned by
its repository and is excluded from this ELMS rehearsal. A failed preflight,
capacity check, smoke check, or redaction check blocks promotion.

The scheduled unit performs the lifecycle in this order: capacity and
credential gates, encrypted `restic backup`, then `restic check`. The status
file is written atomically as `running`/`verifying`; it becomes promotion
evidence only as `verified` after both commands succeed. A failed or interrupted
run is therefore not fresh evidence. The password file must be root-owned or
otherwise mode `0600`-compatible and is never printed.

For an operator-managed installation, enable the supplied daily unit after
placing the non-secret environment file at `/etc/elms/backup.env`:

```bash
sudo systemctl enable --now elms-backup.timer
sudo systemctl start elms-backup.service
sudo python scripts/infra/backup_runner.py report \
  --last-success /var/lib/elms-backup/verified-status.json \
  --max-age-hours 24
```

Promotion consumes the semantic status objects, not path presence. Configure
both `ELMS_BACKUP_EVIDENCE` and `ELMS_VAULT_EVIDENCE` explicitly for the
deployment wrapper. The first points to the verified backup status above; the
second points to the redacted `PASS` marker produced by the Vault preflight
handoff. The wrapper rejects stale, future, failed, pending, or unverified
backup status and rejects any Vault marker other than `PASS`.

Never restore into the host Docker volume root or an active `elms-prod` project;
the preflight rejects both paths, symlink-resolved targets, and existing
directories without a disposable marker. The runner never prunes a repository
or deletes a Docker volume. A stale or unverified external backup is a release
blocker.

## Release and rollback

CI builds the Frappe and Keycloak images, captures their registry digests, and
uploads a non-secret release manifest. Production deployment requires the
protected GitHub `production` environment, an explicit `user@host` target
pinned by the supplied `known_hosts` file, and the server-side allowlisted
wrapper. The wrapper performs a fixed Compose config/pull/up sequence with a
lock; it does not build from a checkout, run arbitrary SSH commands, or remove
state volumes. A development target is never inferred from a missing value and
must not reuse the production target.

```bash
python scripts/infra/check_release_manifest.py --manifest release-manifest.json
python scripts/infra/deploy_wrapper.py --help
```

The protected workflow supplies `ELMS_DEPLOY_TARGET`, `ELMS_DEPLOY_ROOT`, and
`ELMS_DEPLOY_WRAPPER`; all three are explicit remote inputs and the SSH client
uses `StrictHostKeyChecking=yes`. The wrapper also requires `--root` and
`--target`, validates the release Compose hash, and consumes fresh verified
backup plus redacted Vault preflight evidence before any state-changing
command.

Rollback is invoked with the previous verified manifest as a complete image
pair. A failed new health check leaves the previous manifest available and
does not publish the candidate as `current.json`; a subsequent rollback never
mixes a new backend with an old frontend. The disposable failure fixture
`tests/infra/fixtures/release-rollback-failure.json` records only status-level
evidence for this branch. State volumes remain untouched throughout.

## Edge cutover

The public Caddy overlay is separate from the canonical Compose graph. First
run the artifact and listener preflight:

```bash
python scripts/infra/edge_cutover.py preflight --staged
python scripts/infra/edge_cutover.py status
```

Only after fresh release, Vault, backup/restore, staged-smoke and rollback
evidence exists may an owner approve an explicit 80/443 switch. DNS, firewall,
host-Caddy ownership, ACME state and the rollback window must be recorded in
the predecessor evidence file. The cutover gate expects non-secret status
objects for `release: passed`, `vault: passed`, `backup: fresh`,
`staged: passed`, `rollback: passed`, plus `owner_approved: true`; the file
mtime must be fresh (<= 24h). Cutover operations serialize execution via flock
locking on `ELMS_EDGE_LOCK` and strictly refuse switch attempts if ports 80
or 443 are occupied prior to host edge release. No CI push performs this
switch automatically.

### Maintenance window and rollback budget

Edge cutover operations must be executed within a planned maintenance window
with a strictly bounded rollback budget:

- **Maintenance window**: Scheduled off-peak window (minimum 60 minutes)
  approved by operations leadership with an active operator session.
- **Rollback budget**: 15 minutes allocated for route verification and rollback.
  If public listener validation or route health checks fail, the operator must
  trigger rollback immediately within the budget.

### Execution commands

Both switch and rollback commands are fail-closed and strictly require both
`--approved` and `--execute` flags along with fresh predecessor evidence:

```bash
# 1. Preflight status and port check
python scripts/infra/edge_cutover.py preflight --staged
python scripts/infra/edge_cutover.py status

# 2. Explicit switch (requires owner approval and fresh predecessor evidence)
python scripts/infra/edge_cutover.py switch \
    --approved \
    --execute \
    --predecessor-evidence tests/infra/fixtures/edge-evidence.json

# 3. Explicit rollback (stops container Caddy, releases ports, restores host Caddy)
python scripts/infra/edge_cutover.py rollback \
    --approved \
    --execute \
    --predecessor-evidence tests/infra/fixtures/edge-evidence.json
```

### Rollback restoration sequence

Rollback execution:
1. Acquires the serialized cutover lock on `ELMS_EDGE_LOCK`.
2. Stops container Caddy via `docker compose -f docker/compose.prod.yaml -f docker/compose.prod.edge.yaml stop caddy`, releasing public ports 80 and 443.
3. Restores host Caddy by executing `systemctl start caddy`.
4. Verifies host Caddy service health by executing `systemctl is-active --quiet caddy`.
5. Emits structured JSON verification `{"action": "rollback", "executed": true}`.

The disposable drill contract proves this container stop and systemd restoration sequence without performing privileged host mutations in test environments.

