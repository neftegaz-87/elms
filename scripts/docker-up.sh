#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

MODE="dev"
case "${1:-}" in
  dev|prod)
    MODE="$1"
    shift
    ;;
  -h|--help)
    echo "Usage: $0 [dev|prod] [docker compose args...]"
    exit 0
    ;;
esac

if [[ $# -eq 0 ]]; then
  set -- up -d --build
fi

case "$MODE" in
  dev)
    COMPOSE_FILE="docker/compose.dev.yaml"
    ENV_FILE="docker/.env.dev"
    ENV_EXAMPLE="docker/.env.dev.example"
    ;;
  prod)
    COMPOSE_FILE="docker/compose.prod.yaml"
    ENV_FILE="docker/.env.prod"
    ENV_EXAMPLE="docker/.env.prod.example"
    ;;
  *)
    echo "Usage: $0 [dev|prod] [docker compose args...]" >&2
    exit 1
    ;;
esac

if [[ ! -r "$COMPOSE_FILE" ]]; then
  echo "ERROR: missing or unreadable $COMPOSE_FILE" >&2
  exit 1
fi

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

compose() {
  docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" "$@"
}

echo ">>> docker compose -f $COMPOSE_FILE --env-file $ENV_FILE $*"
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
