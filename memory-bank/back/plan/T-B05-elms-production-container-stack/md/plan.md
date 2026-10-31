# [T-B05-elms-production-container-stack] PLAN

**Дата:** 2026-10-31  
**Режим:** BACK/DEVOPS PLAN  
**Уровень:** L3  
**Статус:** active  
**Перенос:** адаптировано из `T-NF-005-prod-container-stack` для ELMS.

## Context

ELMS уже имеет dev/prod Compose с Frappe, MariaDB, Redis, Keycloak и Caddy. Исходный Neftegaz-план был про другой runtime: PostgreSQL/Qdrant/Ollama и собственный backend. В ELMS эти сервисы не переносятся. Review service остаётся внешней first-party boundary и доступен через `ELMS_REVIEW_URL` + signed one-time handoff.

## Dependencies

- `T-B01` — Docker/Frappe foundation.
- `T-B03` — Keycloak/Yandex SSO contract.
- Blocks: `T-B06`, `T-B07`, `T-B08`, `T-B09`.

## Functional requirements

- **FR-001:** canonical `docker/compose.prod.yaml` не содержит build context и source-code mounts; локальная сборка живёт в отдельном `docker/compose.prod.build.yaml`.
- **FR-002:** production service graph включает Frappe web, frontend nginx, websocket, workers, scheduler, MariaDB, Redis cache/queue, Keycloak и Keycloak PostgreSQL.
- **FR-003:** только staged Caddy публикует localhost/high ports; DB, Redis, backend, frontend, Keycloak и Vault не публикуют host ports.
- **FR-004:** mandatory services имеют healthcheck/readiness, restart policy и bounded resources.
- **FR-005:** production image identity — commit/release tag plus digest; `latest` запрещён policy-check.
- **FR-006:** `ELMS_SSO_REQUIRE`, `ELMS_REVIEW_HANDOFF_SECRET` и review URL проходят fail-closed validation; dev synthetic env не меняется.

## Runtime/service graph

The canonical graph is a single ELMS production project. `private` is an
internal Docker network; `edge` is only the container-to-Caddy network and is
not a host publication by itself.

| Service | Responsibility | Readiness/dependency boundary | Host port |
|---|---|---|---|
| `vault` | Vault Raft server | Vault status; no public listener | none |
| `vault-agent` | AppRole auth and protected template render | all four rendered artifacts exist; depends on `vault` | none |
| `db` | Frappe MariaDB | `healthcheck.sh`; depends on Vault render | none |
| `redis-cache` | transient Frappe cache | `redis-cli ping` | none |
| `redis-queue` | durable Frappe queue | `redis-cli ping`; named volume | none |
| `configurator` | writes common Frappe config | one-shot success after DB/Redis health | none |
| `create-site` | creates/migrates site and installs ELMS | one-shot success after config/Vault/DB/Redis | none |
| `backend` | Frappe HTTP application | `/login`; depends on configurator/create-site/Vault | none |
| `frontend` | Nginx static/proxy surface | `/login`; depends on backend/websocket | none |
| `websocket` | Socket.IO | starts only after backend contract | none |
| `queue-short`, `queue-long` | Frappe workers | depend on backend runtime boundary | none |
| `scheduler` | Frappe scheduler | depend on backend runtime boundary | none |
| `keycloak-db` | Keycloak PostgreSQL | `pg_isready`; depends on Vault render | none |
| `keycloak` | SSO broker and realm | `/health/ready`; depends on Keycloak DB/Vault | none |
| `caddy` | staged/edge HTTP entrypoint | `/healthz`; depends on frontend/Keycloak | staged localhost only |

The external review service is not a Compose service in ELMS. ELMS owns only
the `ELMS_REVIEW_URL` validation and the signed, short-lived, one-time handoff
(`ELMS_REVIEW_HANDOFF_SECRET` is rendered by Vault and never placed in git or
plain Compose YAML).

## Image, overlay, and exposure contract

- `docker/compose.prod.yaml` is the production SoT and contains images,
  named volumes, health/readiness, dependencies, networks, and non-secret
  metadata only. It has no `build:` and no application checkout mounts.
- `docker/compose.prod.build.yaml` is local/CI-only and adds build contexts
  for the ELMS and Keycloak images. It is never used by a production host
  deploy wrapper.
- `docker/compose.prod.staged.yaml` changes only the rehearsal hostname and
  binds Caddy to `127.0.0.1:${STAGED_HTTP_PUBLISH_PORT:-18080}`.
- `docker/compose.prod.edge.yaml` is an explicit owner-approved public-port
  overlay. It is not a default and no CI job performs a cutover.
- DB, Redis, Frappe, frontend, Keycloak, Vault and Vault Agent use `expose` or
  internal networking only. A host `ports:` entry on any of them is a policy
  failure.
- Release images use a commit/release tag and a registry digest. A manifest
  must bind the image pair and Compose hash to one commit; `latest`, `dev`,
  secret-like fields, and mismatched image pairs are rejected.

## Readiness, resource, and security contract

Every long-running mandatory service has `restart: unless-stopped` (or the
one-shot equivalent), `security_opt: no-new-privileges:true`, and a bounded
`deploy.resources.limits` block. The required healthchecks are:

- MariaDB `healthcheck.sh --connect --innodb_initialized`;
- Redis cache/queue `redis-cli ping`;
- Keycloak PostgreSQL `pg_isready`;
- Keycloak `/health/ready`;
- Frappe backend/frontend `/login`;
- Vault/Vault Agent render readiness;
- Caddy `/healthz`.

`backend` is not eligible for healthy promotion until `configurator` and
`create-site` complete successfully and Vault Agent reports all required
rendered files. A failed one-shot or unhealthy dependency is a non-zero gate,
not a warning or a fallback to an old path.

## Secret and review boundary

`docker/.env.prod.example` contains only hostnames, image refs/tags, paths to
root-owned AppRole files, listener settings and non-secret application
metadata. The following values are Vault-owned: Frappe DB/admin credentials,
Keycloak DB/admin/client/fallback credentials, Yandex client secret, review
handoff secret, and the external review client secret. Vault Agent templates
use `error_on_missing_key = true`; MariaDB and Keycloak PostgreSQL consume
password files.

In production, `ELMS_REVIEW_URL` must be an absolute HTTPS URL without user
info, fragments, or control characters. `ELMS_REVIEW_ALLOW_HTTP=1` is allowed
only by the staged overlay. The ELMS handoff endpoint requires the Vault
secret, compares it in constant time, consumes the ticket once, and rejects
missing/expired/invalid tickets. Dev synthetic values remain in the dev
Compose contract and are not copied into production.

## Verification matrix

| ID | Contract | Targeted evidence |
|---|---|---|
| FR-001/FR-002 | image-only graph and complete services | merged staged Compose config plus service-set assertion |
| FR-003 | no internal host exposure | canonical Compose policy and overlay inspection |
| FR-004 | readiness/resources/security | policy validator plus dependency/health assertions |
| FR-005 | tag+digest release identity | release fixture pass and latest/secret negative fixture |
| FR-006 | Vault/SSO/review fail-closed | secret contract, Vault dry-run, review handoff tests |
| AC-NEG-001 | missing production metadata | preflight with required setting removed exits non-zero |
| AC-NEG-002 | forbidden build/mount/port/latest | mutated Compose/manifest fixtures are rejected |
| AC-NEG-003 | unhealthy/failed one-shot | `depends_on` health/success conditions and staged smoke gate |
| AC-NEG-004 | review misconfiguration | URL/secret validation and one-time handoff tests |

The full application suite, live staged run, Vault bootstrap, backup restore,
registry push, deploy/rollback and public edge switch are BACK QA or operator
gates after implementation; they are not silently represented as a dry-run
pass.

## Acceptance / negative cases

- **AC-NEG-001:** Missing required prod env → non-zero before Compose changes.
- **AC-NEG-002:** `latest`, source mount, `build:` в canonical prod или host DB/Redis/Keycloak port → policy failure.
- **AC-NEG-003:** Unhealthy MariaDB/Redis/Keycloak or failed `create-site` → no backend promotion.
- **AC-NEG-004:** Review URL missing/HTTP in prod or handoff secret missing → integration path refuses access, no fake success.

## Implementation slices

1. Split immutable prod Compose from local build and staged/edge overrides.
2. Add service health, networks, resource/security policy and release image validation.
3. Add isolated smoke and regression tests for dev/prod contract.

## Replacement / sunset

This is a brownfield production-boundary replacement. The old production path
mixed checkout builds, mutable image defaults, direct secret interpolation and
public Caddy ownership into one Compose file. The new path must be the only
production path; staged rehearsal and local/CI builds are explicit overlays.

### A — code/config contracts

| Old symbol/contract | Replacement | Policy |
|---|---|---|
| `docker/compose.prod.yaml::x-image.build` | image-only canonical Compose plus `docker/compose.prod.build.yaml` | delete in-epic |
| `docker/compose.prod.yaml` direct `DB_PASSWORD`, `KEYCLOAK_DB_PASSWORD`, `KEYCLOAK_CLIENT_SECRET` interpolation | Vault Agent rendered files and `*_PASSWORD_FILE` delivery | delete in-epic |

### B — entrypoints/deploy surfaces

| Old entrypoint | Replacement | Policy |
|---|---|---|
| canonical `docker/compose.prod.yaml` build-from-checkout invocation | production pull/config/up from image-only Compose; build remains only in explicit build overlay | delete in-epic |
| canonical Caddy `ports: 80/443` bindings | `compose.prod.staged.yaml` localhost/high port and explicit `compose.prod.edge.yaml` | delete in-epic |

### C — fallbacks/soft-fail

| Old fallback | Replacement | Policy |
|---|---|---|
| mutable `latest`, `dev`, or `prod-local` image fallback | fail-closed image policy and tag+digest release manifest | delete in-epic |
| direct Compose secret values and missing Vault render treated as startable | Vault Agent readiness and non-zero preflight before promotion | delete in-epic |
| missing/HTTP production review URL or missing handoff secret treated as usable | `ELMS_REVIEW_URL`/handoff contract rejects access; HTTP is staged-only | delete in-epic |
| staged smoke reusing public ports or live production project/data | isolated localhost/high-port staged project with scoped cleanup | delete in-epic |

### I — instruction surfaces

| Old instruction | Replacement | Policy |
|---|---|---|
| `docker/README.md` instructions to copy production passwords into `.env.prod` and run the mixed prod file | runbook for non-secret env, Vault preflight, image-only production, and isolated staged smoke | rewrite in-epic |
| Makefile/scripts instructions that imply public ports or checkout build is the default production path | explicit staged target and owner-approved edge/deploy commands | rewrite in-epic |

The final implementation step includes the complete A/B/C/I inventory scan and
targeted regression evidence. No live Vault bootstrap, public cutover, or
production data operation is performed by this epic.

## Verification

```bash
docker compose --env-file docker/.env.prod -f docker/compose.prod.yaml -f docker/compose.prod.build.yaml -f docker/compose.prod.staged.yaml config --quiet
python3 scripts/infra/check_compose_policy.py --file docker/compose.prod.yaml
bash scripts/infra/compose_smoke.sh --profile staged --dry-run
```

## ELMS implementation status

Implemented in this repository: canonical image-only Compose graph, local/CI
build overlay, isolated staged/edge overlays, internal networks, healthchecks,
resource/security defaults, Vault render gate, release image-ref override,
policy checker, and staged smoke runner. The live staged run remains gated on
real Vault AppRole files and non-placeholder production metadata.

Public Caddy and real production data remain outside this epic.
