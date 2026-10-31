#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ENV_FILE="$ROOT_DIR/docker/.env.prod"
ROLE_ID_FILE=""
SECRET_ID_FILE=""
ACTION="bootstrap"
FIXTURE_FILE=""

usage() {
  cat <<'EOF'
Usage: vault_bootstrap.sh [bootstrap|rotate|revoke] [options]

Actions configure the ELMS Vault AppRole, rotate its secret ID, or revoke the
secret ID currently held in the protected file. Use --fixture for a disposable
synthetic rehearsal; fixture output is status-only and redacted.

Options:
  --env-file PATH          production metadata dotenv file
  --role-id-file PATH      root-owned AppRole role-id destination
  --secret-id-file PATH    root-owned AppRole secret-id destination
  --fixture PATH           synthetic state fixture; does not contact Docker

The operator credential is supplied as ELMS_VAULT_OPERATOR_TOKEN. Vault
initialization, unseal, and recovery-key custody remain manual operations.
EOF
}

if [[ "${1:-}" == "bootstrap" || "${1:-}" == "rotate" || "${1:-}" == "revoke" ]]; then
  ACTION="$1"
  shift
fi

while [[ $# -gt 0 ]]; do
  case "$1" in
    --env-file)
      [[ $# -ge 2 ]] || { echo "ERROR: --env-file needs a path" >&2; exit 2; }
      ENV_FILE="$2"
      shift 2
      ;;
    --role-id-file)
      [[ $# -ge 2 ]] || { echo "ERROR: --role-id-file needs a path" >&2; exit 2; }
      ROLE_ID_FILE="$2"
      shift 2
      ;;
    --secret-id-file)
      [[ $# -ge 2 ]] || { echo "ERROR: --secret-id-file needs a path" >&2; exit 2; }
      SECRET_ID_FILE="$2"
      shift 2
      ;;
    --fixture)
      [[ $# -ge 2 ]] || { echo "ERROR: --fixture needs a path" >&2; exit 2; }
      FIXTURE_FILE="$2"
      shift 2
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

if [[ -n "$FIXTURE_FILE" ]]; then
  [[ -r "$FIXTURE_FILE" ]] || { echo "ERROR: cannot read synthetic Vault fixture" >&2; exit 1; }
  python3 - "$FIXTURE_FILE" "$ACTION" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
action = sys.argv[2]
try:
    payload = json.loads(path.read_text(encoding="utf-8"))
except (OSError, json.JSONDecodeError) as exc:
    print(f"ERROR: invalid synthetic Vault fixture: {exc}", file=sys.stderr)
    raise SystemExit(1)

if not isinstance(payload, dict):
    print("ERROR: synthetic Vault fixture must be an object", file=sys.stderr)
    raise SystemExit(1)

status = str(payload.get("status", "ready")).lower()
if status in {"sealed", "unavailable", "unauthorized", "missing", "incomplete"}:
    print(f"ERROR: synthetic Vault state is fail-closed: {status}", file=sys.stderr)
    raise SystemExit(1)

print(f"PASS: synthetic Vault {action} rehearsal completed (values redacted)")
PY
  exit 0
fi

[[ -r "$ENV_FILE" ]] || { echo "ERROR: cannot read $ENV_FILE" >&2; exit 1; }
[[ -n "${ELMS_VAULT_OPERATOR_TOKEN:-}" ]] || {
  echo "ERROR: operator credential must be supplied by the operator environment" >&2
  exit 1
}
command -v docker >/dev/null 2>&1 || { echo "ERROR: docker is required" >&2; exit 1; }

dotenv_value() {
  local wanted="$1"
  awk -v wanted="$wanted" '
    /^[[:space:]]*#/ || /^[[:space:]]*$/ { next }
    {
      line=$0
      sub(/^[[:space:]]+/, "", line)
      split(line, pair, "=")
      if (pair[1] == wanted) {
        value=substr(line, index(line, "=") + 1)
        sub(/[[:space:]]+#.*$/, "", value)
        gsub(/^['"'"']|['"'"']$/, "", value)
        print value
        exit
      }
    }
  ' "$ENV_FILE"
}

if [[ -z "$ROLE_ID_FILE" ]]; then
  ROLE_ID_FILE="$(dotenv_value VAULT_ROLE_ID_FILE)"
fi
if [[ -z "$SECRET_ID_FILE" ]]; then
  SECRET_ID_FILE="$(dotenv_value VAULT_SECRET_ID_FILE)"
fi
[[ -n "$ROLE_ID_FILE" && -n "$SECRET_ID_FILE" ]] || {
  echo "ERROR: AppRole file paths are required" >&2
  exit 1
}

root_dir_real="$(cd "$ROOT_DIR" && pwd -P)"
for path in "$ROLE_ID_FILE" "$SECRET_ID_FILE"; do
  [[ "$path" = /* ]] || { echo "ERROR: AppRole file path must be absolute" >&2; exit 1; }
  resolved="$(readlink -m -- "$path")"
  case "$resolved" in
    "$root_dir_real"|"$root_dir_real"/*)
      echo "ERROR: AppRole file must live outside the repository" >&2
      exit 1
      ;;
  esac
  [[ ! -L "$path" ]] || { echo "ERROR: AppRole file must not be a symlink" >&2; exit 1; }
done

compose=(docker compose --env-file "$ENV_FILE" -f "$ROOT_DIR/docker/compose.prod.yaml")
vault_exec() {
  "${compose[@]}" exec -T -e ELMS_VAULT_OPERATOR_TOKEN vault \
    sh -ec 'exec vault -token="$ELMS_VAULT_OPERATOR_TOKEN" "$@"' -- "$@"
}

write_protected() {
  local destination="$1"
  local temporary
  install -d -m 700 "$(dirname "$destination")"
  temporary="$(mktemp "${destination}.partial.XXXXXX")"
  trap 'rm -f -- "$temporary"' RETURN
  umask 077
  cat > "$temporary"
  chmod 600 "$temporary"
  mv -- "$temporary" "$destination"
  trap - RETURN
}

bootstrap() {
  vault_exec status >/dev/null
  if ! vault_exec secrets list 2>/dev/null | grep '^elms/' >/dev/null; then
    vault_exec secrets enable -path=elms kv-v2 >/dev/null
  fi
  vault_exec policy write elms-agent /vault/policies/elms-agent.hcl >/dev/null
  if ! vault_exec auth list 2>/dev/null | grep '^approle/' >/dev/null; then
    vault_exec auth enable approle >/dev/null
  fi
  vault_exec write auth/approle/role/elms-agent \
    token_policies=elms-agent token_type=batch token_ttl=1h token_max_ttl=4h >/dev/null
  write_protected "$ROLE_ID_FILE" < <(vault_exec read -field=role_id auth/approle/role/elms-agent/role-id)
  write_protected "$SECRET_ID_FILE" < <(vault_exec write -field=secret_id -f auth/approle/role/elms-agent/secret-id)
  echo "PASS: Vault KV/AppRole contract installed; protected IDs were written (values redacted)"
}

rotate() {
  [[ -s "$ROLE_ID_FILE" && -s "$SECRET_ID_FILE" ]] || {
    echo "ERROR: existing AppRole files are required before rotation" >&2
    exit 1
  }
  old_secret_id="$(<"$SECRET_ID_FILE")"
  new_secret_file="$(mktemp "${SECRET_ID_FILE}.rotate.XXXXXX")"
  trap 'rm -f -- "$new_secret_file"' RETURN
  umask 077
  vault_exec write -field=secret_id -f auth/approle/role/elms-agent/secret-id > "$new_secret_file"
  chmod 600 "$new_secret_file"
  vault_exec write auth/approle/role/elms-agent/secret-id/destroy "secret_id=$old_secret_id" >/dev/null
  mv -- "$new_secret_file" "$SECRET_ID_FILE"
  trap - RETURN
  echo "PASS: AppRole secret ID rotated and previous ID revoked (values redacted)"
}

revoke() {
  [[ -s "$SECRET_ID_FILE" ]] || {
    echo "ERROR: existing secret-id file is required for revoke" >&2
    exit 1
  }
  secret_id="$(<"$SECRET_ID_FILE")"
  vault_exec write auth/approle/role/elms-agent/secret-id/destroy "secret_id=$secret_id" >/dev/null
  rm -f -- "$SECRET_ID_FILE"
  echo "PASS: AppRole secret ID revoked; startup remains blocked until a new ID is provisioned"
}

case "$ACTION" in
  bootstrap) bootstrap ;;
  rotate) rotate ;;
  revoke) revoke ;;
esac
