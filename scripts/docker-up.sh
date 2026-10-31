#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

MODE="dev"
case "${1:-}" in
  dev|prod|prod-edge)
    MODE="$1"
    shift
    ;;
  -h|--help)
    echo "Usage: $0 [dev|prod|prod-edge] [docker compose args...]"
    echo "  prod      staged localhost/high-port stack (base + build + staged overlay)"
    echo "  prod-edge owner-approved public 80/443 stack (set ELMS_EDGE_APPROVED=1)"
    exit 0
    ;;
esac

if [[ $# -eq 0 ]]; then
  if [[ "$MODE" == "prod-edge" ]]; then
    set -- up -d
  else
    set -- up -d --build
  fi
fi

COMPOSE_FILES=()
PROJECT_OVERRIDE=""
case "$MODE" in
  dev)
    COMPOSE_FILES=("docker/compose.dev.yaml")
    ENV_FILE="docker/.env.dev"
    ENV_EXAMPLE="docker/.env.dev.example"
    ;;
  prod)
    COMPOSE_FILES=("docker/compose.prod.yaml" "docker/compose.prod.build.yaml" "docker/compose.prod.staged.yaml")
    ENV_FILE="docker/.env.prod"
    ENV_EXAMPLE="docker/.env.prod.example"
    PROJECT_OVERRIDE="${ELMS_STAGE_PROJECT_NAME:-elms-prod-stage}"
    ;;
  prod-edge)
    COMPOSE_FILES=("docker/compose.prod.yaml" "docker/compose.prod.edge.yaml")
    ENV_FILE="docker/.env.prod"
    ENV_EXAMPLE="docker/.env.prod.example"
    if [[ "${ELMS_EDGE_APPROVED:-0}" != "1" ]]; then
      echo "ERROR: prod-edge is gated; set ELMS_EDGE_APPROVED=1 after owner approval" >&2
      exit 1
    fi
    ;;
  *)
    echo "Usage: $0 [dev|prod|prod-edge] [docker compose args...]" >&2
    exit 1
    ;;
esac

for compose_file in "${COMPOSE_FILES[@]}"; do
  if [[ ! -r "$compose_file" ]]; then
    echo "ERROR: missing or unreadable $compose_file" >&2
    exit 1
  fi
done

if [[ ! -r "$ENV_EXAMPLE" || ! -s "$ENV_EXAMPLE" ]]; then
  echo "ERROR: missing or empty $ENV_EXAMPLE" >&2
  exit 1
fi

if [[ ! -f "$ENV_FILE" && -f "$ENV_EXAMPLE" ]]; then
  cp "$ENV_EXAMPLE" "$ENV_FILE"
  echo "Created $ENV_FILE from $ENV_EXAMPLE"
fi

if [[ ! -r "$ENV_FILE" || ! -s "$ENV_FILE" ]]; then
  echo "ERROR: missing or empty $ENV_FILE" >&2
  exit 1
fi

if [[ "$MODE" == "prod" ]]; then
  if [[ -z "$PROJECT_OVERRIDE" || "$PROJECT_OVERRIDE" == "elms-prod" ]]; then
    echo "ERROR: staged production mode requires a project name distinct from elms-prod" >&2
    exit 1
  fi
  staged_port="${STAGED_HTTP_PUBLISH_PORT:-$(awk -F= '/^[[:space:]]*STAGED_HTTP_PUBLISH_PORT[[:space:]]*=/{print $2; exit}' "$ENV_FILE")}"
  staged_port="${staged_port:-18080}"
  if ! [[ "$staged_port" =~ ^[0-9]+$ ]] || (( staged_port < 1024 )); then
    echo "ERROR: staged production mode requires a numeric high port (>=1024)" >&2
    exit 1
  fi
fi

compose() {
  local command=(docker compose --env-file "$ENV_FILE")
  if [[ -n "$PROJECT_OVERRIDE" ]]; then
    command+=(--project-name "$PROJECT_OVERRIDE")
  fi
  for compose_file in "${COMPOSE_FILES[@]}"; do
    command+=(-f "$compose_file")
  done
  "${command[@]}" "$@"
}

preflight() {
  if [[ -n "$PROJECT_OVERRIDE" ]]; then
    COMPOSE_PROJECT_NAME="$PROJECT_OVERRIDE" bash scripts/infra/vault_preflight.sh --env-file "$ENV_FILE" "$@"
  else
    bash scripts/infra/vault_preflight.sh --env-file "$ENV_FILE" "$@"
  fi
}

is_up_request=0
for arg in "$@"; do
  [[ "$arg" == "up" ]] && is_up_request=1
done
if [[ "$is_up_request" -eq 1 && "$MODE" == "prod-edge" ]]; then
  echo "ERROR: public edge promotion must use make prod.edge.up / edge_cutover.py with predecessor evidence" >&2
  exit 1
fi
if [[ "$is_up_request" -eq 1 && ( "$MODE" == "prod" || "$MODE" == "prod-edge" ) ]]; then
  python3 scripts/infra/check_compose_policy.py --file docker/compose.prod.yaml
  python3 scripts/infra/check_secret_contract.py
  compose config --quiet
  preflight --dry-run
  echo ">>> Vault services (authenticated render gate) [$MODE]"
  compose up -d vault vault-agent
  preflight
fi

echo ">>> docker compose $MODE ($ENV_FILE) $*"
compose "$@"

is_up=0
detached=0
for arg in "$@"; do
  if [[ "$arg" == "up" ]]; then
    is_up=1
  fi
  if [[ "$arg" == "-d" || "$arg" == "--detach" ]]; then
    detached=1
  fi
done

if [[ "$is_up" -eq 1 ]]; then
  # create-site is a one-shot: compose up does not re-run it after success.
  # Force sync on every up so site creation/migration always applies.
  echo ">>> site sync (migrate) [$MODE]"
  if [[ "$detached" -eq 1 ]]; then
    compose up -d --force-recreate --no-deps create-site
    cid="$(compose ps -a -q create-site | head -n1)"
    if [[ -z "$cid" ]]; then
      echo "ERROR: create-site container not found after up" >&2
      exit 1
    fi
    echo ">>> waiting for create-site ($cid) without attaching logs…"
    exit_code="$(docker wait "$cid")"
    if [[ "$exit_code" != "0" ]]; then
      echo "ERROR: site sync failed (exit $exit_code). Logs:" >&2
      compose logs --no-color --tail 80 create-site >&2
      exit "$exit_code"
    fi
    echo ">>> site sync complete (logs: ./scripts/docker-up.sh $MODE logs create-site)"
  else
    compose up --force-recreate --no-deps create-site
  fi
fi
