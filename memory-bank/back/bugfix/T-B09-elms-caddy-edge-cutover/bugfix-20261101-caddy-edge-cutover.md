# Bugfix: resolve edge rollback, forced-failure restoration, and HTTP 404 fallback gaps

- **Epic ID:** T-B09-elms-caddy-edge-cutover
- **Role:** BACK
- **Source QA:** `memory-bank/back/qa/T-B09-elms-caddy-edge-cutover/qa-20261101-caddy-edge-cutover.yaml`
- **Queue:** `memory-bank/back/bugfix/T-B09-elms-caddy-edge-cutover/bugfix-queue.yaml`
- **Status:** PASS — BF-001, BF-002, and BF-003 closed

## Root Cause

During initial QA verification of epic T-B09 (Caddy Edge Cutover), three contract gaps were identified:
1. **BF-001 (FR-005):** In `scripts/infra/edge_cutover.py`, the rollback sequence stopped the container Caddy and started host Caddy via `systemctl start caddy`, verifying only `systemctl is-active`. It lacked old route runtime verification.
2. **BF-002 (Done when):** The switch execution handler did not automatically trigger restoration and prove the old edge upon encountering a failure during edge activation.
3. **BF-003 (RC-003):** Public HTTP blocks for `http://{$SITE_NAME}` and `http://{$AUTH_HOSTNAME}` in `docker/caddy/Caddyfile` matched only `/healthz` and lacked an explicit `handle` fallback returning HTTP 404 for unmatched paths.

## Changes Implemented

- **`scripts/infra/edge_cutover.py`**:
  - Implemented centralized helper `restore_host_edge` that stops the container Caddy, starts host Caddy via systemd, checks `systemctl is-active --quiet caddy`, and verifies the old route via `curl --fail --silent --show-error http://127.0.0.1/healthz`.
  - Updated the `switch` action in `execute` to wrap container startup in a `try...except` block, automatically invoking `restore_host_edge` upon failure.
  - Used `restore_host_edge` in the `rollback` action to ensure consistent restoration and verification.
  - Added robust default lock path resolution (`default_lock_path`) handling unwritable `/run/lock` environments.
  - Enforced preflight validation prior to executing switch or rollback operations.

- **`docker/caddy/Caddyfile`**:
  - Added explicit `handle @health { respond 200 }` and `handle { respond "Not Found" 404 }` blocks to both `http://{$SITE_NAME}` and `http://{$AUTH_HOSTNAME}` public HTTP server definitions.
  - Added `@health path /healthz` responder to HTTPS blocks.

- **`tests/infra/test_production_contracts.py`**:
  - Added `fake_curl` mock harness capturing curl invocations during simulated drills.
  - Enhanced `test_edge_rollback_drill_contract` to assert that `curl http://127.0.0.1/healthz` is executed during rollback.
  - Updated `test_caddy_staged_and_edge_routing_contract` to verify explicit 404 fallback handling and regex matches for HTTP server blocks.

Changed paths:
- `docker/caddy/Caddyfile`
- `scripts/infra/edge_cutover.py`
- `tests/infra/test_production_contracts.py`

## Verification

```bash
python3 -m pytest -q tests/infra/test_production_contracts.py
```
Result: `21 passed in 1.41s` (exit code 0).

```bash
bin/pytest -q --tb=line
```
Result: `91 passed, 2 skipped in 0.23s` (exit code 0).

