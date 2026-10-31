# [T-B09-elms-caddy-edge-cutover] PLAN

**Дата:** 2026-10-31  
**Режим:** BACK/DEVOPS PLAN  
**Уровень:** L3  
**Статус:** active  
**Перенос:** адаптировано из `T-NF-009-caddy-edge-cutover` для ELMS.

## Dependencies

`T-B05` staged stack, `T-B06` Vault, `T-B07` verified backup/restore, `T-B08` release/rollback. Нужны отдельные maintenance window и rollback budget.

## Route contract

- ELMS/Frappe host → `frontend:8080`.
- Auth host → `keycloak:8080`.
- Review handoff URL остаётся first-party review service contract и не превращается в catch-all proxy.
- `/healthz` — explicit edge health; неизвестные host/path не получают fake `200`.

## Requirements

- **FR-001:** staged Caddy binds only localhost/high ports and does not alter DNS, firewall or host Caddy.
- **FR-002:** public switch requires fresh predecessor evidence, owner approval and serialized lock.
- **FR-003:** container Caddy is sole 80/443 owner after switch; DB/Redis/backend/Keycloak/Vault remain private.
- **FR-004:** Caddy owns persistent ACME state; host private keys are never copied.
- **FR-005:** rollback releases container ports, restores host Caddy and verifies old route.

## Implementation slices

1. Staged Caddyfile, high-port compose override and route smoke.
2. Gate verifier with port/TLS/config evidence.
3. Explicit edge wrapper and disposable rollback drill.

## Verification

```bash
python3 scripts/infra/edge_cutover.py preflight --staged
python3 scripts/infra/edge_cutover.py status
```

## ELMS implementation status

Implemented in this repository: explicit staged/public Caddyfiles, localhost
high-port overlay, edge ownership preflight, fresh predecessor-evidence
schema, serialized cutover lock, occupied-port refusal, owner/execute gate,
and fixed Caddy stop/systemd rollback path. DNS, firewall, host-Caddy state,
ACME validation, and a real maintenance-window switch remain intentionally
unexecuted production gates.

Real `80/443` cutover is not executed by CI or by this repository change.
