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
recovery/unseal material. Prepare a real `docker/.env.prod` containing only
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

Start only the Vault service on an isolated maintenance project. Initialize
and unseal it once from the secure operator console, storing recovery material
offline according to the organization's custody policy. Do not put the output
in CI logs, shell history, the repository, or a runtime container.

After Vault is initialized and unsealed, run the fixed bootstrap helper with an
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

```bash
python scripts/infra/backup_runner.py manifest \
  --output /var/lib/elms-backup/elms-backup-manifest.json
python scripts/infra/backup_runner.py restore-preflight \
  --target /var/lib/elms-restore-rehearsal
```

Never restore into `/var/lib/docker/volumes` or an active `elms-prod` project.
The runner never prunes a repository or deletes a Docker volume. A stale or
unverified external backup is a release blocker.

## Release and rollback

CI builds the Frappe and Keycloak images, captures their registry digests, and
uploads a non-secret release manifest. Production deployment requires the
protected GitHub `production` environment and the server-side allowlisted
wrapper. The wrapper performs a fixed Compose config/pull/up sequence with a
lock; it does not build from a checkout, run arbitrary SSH commands, or remove
state volumes.

```bash
python scripts/infra/check_release_manifest.py --manifest release-manifest.json
python scripts/infra/deploy_wrapper.py --help
```

Rollback is invoked with the previous verified manifest as a complete image
pair. A failed new health check leaves the previous manifest available; it
does not mix a new backend with an old frontend.

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
mtime must be fresh. No CI push performs this switch automatically.
