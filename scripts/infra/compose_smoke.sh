#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ENV_FILE="$ROOT_DIR/docker/.env.prod"
ENV_FILE_EXPLICIT=0
PROFILE="staged"
DRY_RUN=0
KEEP=0

usage() {
  cat <<'EOF'
Usage: compose_smoke.sh [--profile staged] [--env-file PATH] [--dry-run] [--keep]

Dry-run validates the merged production/build/staged Compose model. A live run
uses a dedicated Compose project, checks the Frappe and Keycloak routes, and
removes that staged stack on exit unless --keep is supplied.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --profile)
      [[ $# -ge 2 ]] || { echo "ERROR: --profile needs a value" >&2; exit 2; }
      PROFILE="$2"
      shift 2
      ;;
    --env-file)
      [[ $# -ge 2 ]] || { echo "ERROR: --env-file needs a path" >&2; exit 2; }
      ENV_FILE="$2"
      ENV_FILE_EXPLICIT=1
      shift 2
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --keep)
      KEEP=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "ERROR: unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

[[ "$PROFILE" == "staged" ]] || { echo "ERROR: only the staged profile is supported" >&2; exit 2; }
if [[ ! -r "$ENV_FILE" ]]; then
  if [[ "$DRY_RUN" == "1" && "$ENV_FILE_EXPLICIT" == "0" ]]; then
    ENV_FILE="$ROOT_DIR/docker/.env.prod.example"
    echo "INFO: docker/.env.prod is absent; dry-run uses the non-secret production example"
  else
    echo "ERROR: cannot read env file: $ENV_FILE" >&2
    exit 1
  fi
fi
command -v docker >/dev/null 2>&1 || { echo "ERROR: docker is required" >&2; exit 1; }

compose=(
  docker compose
  --env-file "$ENV_FILE"
  -f "$ROOT_DIR/docker/compose.prod.yaml"
  -f "$ROOT_DIR/docker/compose.prod.build.yaml"
  -f "$ROOT_DIR/docker/compose.prod.staged.yaml"
)

project_name="${COMPOSE_PROJECT_NAME:-$(awk -F= '/^[[:space:]]*COMPOSE_PROJECT_NAME[[:space:]]*=/{print $2; exit}' "$ENV_FILE")}"
staged_port="${STAGED_HTTP_PUBLISH_PORT:-$(awk -F= '/^[[:space:]]*STAGED_HTTP_PUBLISH_PORT[[:space:]]*=/{print $2; exit}' "$ENV_FILE")}"
staged_port="${staged_port:-18080}"
if ! [[ "$staged_port" =~ ^[0-9]+$ ]] || (( staged_port < 1024 )); then
  echo "ERROR: staged smoke requires a numeric high port (>=1024)" >&2
  exit 1
fi

"${compose[@]}" config --quiet
echo "PASS: merged staged Compose model"

if [[ "$DRY_RUN" == "1" ]]; then
  "$ROOT_DIR/scripts/infra/vault_preflight.sh" --env-file "$ENV_FILE" --dry-run
  exit 0
fi

"$ROOT_DIR/scripts/infra/vault_preflight.sh" --env-file "$ENV_FILE"

if [[ -z "$project_name" || "$project_name" == "elms-prod" ]]; then
  echo "ERROR: staged smoke requires a separate COMPOSE_PROJECT_NAME (not elms-prod)" >&2
  exit 1
fi

cleanup() {
  if [[ "$KEEP" != "1" ]]; then
    # The project name is required to be staged-only, so removing its volumes
    # cannot touch the production project or production data.
    "${compose[@]}" down --remove-orphans --volumes >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

"${compose[@]}" up -d --build --force-recreate

wait_for_create_site() {
  local container_id="" attempts=60 exit_code
  while (( attempts > 0 )); do
    container_id="$("${compose[@]}" ps -a -q create-site | head -n1)"
    if [[ -n "$container_id" ]]; then
      break
    fi
    attempts=$((attempts - 1))
    sleep 2
  done
  if [[ -z "$container_id" ]]; then
    echo "ERROR: create-site container was not created" >&2
    return 1
  fi

  exit_code="$(docker wait "$container_id")"
  if [[ "$exit_code" != "0" ]]; then
    echo "ERROR: create-site failed (exit $exit_code); backend promotion is blocked" >&2
    "${compose[@]}" logs --no-color --tail 80 create-site >&2 || true
    return 1
  fi
}

wait_for_create_site

site_host="${STAGED_SITE_NAME:-$(awk -F= '/^[[:space:]]*STAGED_SITE_NAME[[:space:]]*=/{print $2; exit}' "$ENV_FILE")}"
site_host="${site_host:-elms.localhost}"
auth_host="${STAGED_AUTH_HOSTNAME:-$(awk -F= '/^[[:space:]]*STAGED_AUTH_HOSTNAME[[:space:]]*=/{print $2; exit}' "$ENV_FILE")}"
auth_host="${auth_host:-auth.localhost}"

wait_for() {
  local url="$1" host="$2" attempts=60
  while (( attempts > 0 )); do
    if curl --fail --silent --show-error -H "Host: $host" "$url" >/dev/null 2>&1; then
      return 0
    fi
    attempts=$((attempts - 1))
    sleep 2
  done
  echo "ERROR: staged route did not become ready: $host" >&2
  return 1
}

wait_for "http://127.0.0.1:${staged_port}/login" "$site_host"
wait_for "http://127.0.0.1:${staged_port}/realms/elms/.well-known/openid-configuration" "$auth_host"
echo "PASS: staged Frappe login and Keycloak discovery routes"
