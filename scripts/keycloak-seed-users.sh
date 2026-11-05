#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

exec bash scripts/docker-up.sh dev exec -T keycloak /opt/keycloak/seed-demo-users.sh
