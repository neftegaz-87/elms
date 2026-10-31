#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ENV_FILE="$ROOT_DIR/docker/.env.prod"
DRY_RUN=0
FIXTURE_FILE=""

usage() {
  cat <<'EOF'
Usage: vault_preflight.sh [--env-file PATH] [--dry-run] [--fixture PATH]

Validate the non-secret production contract. Without --dry-run, also verify
that the operator-managed AppRole files, authenticated Vault state, and Vault
Agent render are available. A JSON fixture exercises the same fail-closed
state checks without contacting Vault. This command never prints secret values.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --env-file)
      [[ $# -ge 2 ]] || { echo "ERROR: --env-file needs a path" >&2; exit 2; }
      ENV_FILE="$2"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=1
      shift
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

[[ -r "$ENV_FILE" ]] || { echo "ERROR: cannot read env file: $ENV_FILE" >&2; exit 1; }

# Read simple dotenv assignments without sourcing the file. Production config
# is operator input and must never be executed as shell code by a preflight.
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
        gsub(/^['\''"]|['\''"]$/, "", value)
        print value
        exit
      }
    }
  ' "$ENV_FILE"
}

required=(
  COMPOSE_PROJECT_NAME CUSTOM_IMAGE CUSTOM_TAG KEYCLOAK_IMAGE KEYCLOAK_TAG
  VAULT_ROLE_ID_FILE VAULT_SECRET_ID_FILE SITE_NAME AUTH_HOSTNAME SITE_HOST_NAME
  KEYCLOAK_PUBLIC_URL ELMS_REVIEW_URL
)
for key in "${required[@]}"; do
  value="$(dotenv_value "$key")"
  if [[ -z "$value" ]]; then
    echo "ERROR: required non-secret setting is missing: $key" >&2
    exit 1
  fi
done

forbidden=(
  DB_PASSWORD ADMIN_PASSWORD KEYCLOAK_DB_PASSWORD KEYCLOAK_ADMIN_PASSWORD
  KEYCLOAK_CLIENT_SECRET
  NEFTEGAZ_REVIEW_CLIENT_SECRET ELMS_REVIEW_HANDOFF_SECRET YANDEX_CLIENT_ID YANDEX_CLIENT_SECRET
)
for key in "${forbidden[@]}"; do
  value="$(dotenv_value "$key")"
  if [[ -n "$value" ]]; then
    echo "ERROR: secret value must not be stored in $ENV_FILE: $key" >&2
    exit 1
  fi
done

review_url="$(dotenv_value ELMS_REVIEW_URL)"
case "$review_url" in
  https://*) ;;
  *)
    echo "ERROR: ELMS_REVIEW_URL must use HTTPS in production" >&2
    exit 1
    ;;
esac

sso_required="$(dotenv_value ELMS_SSO_REQUIRE)"
case "${sso_required:-1}" in
  1|true|TRUE|yes|YES|on|ON) ;;
  *)
    echo "ERROR: ELMS_SSO_REQUIRE must enable mandatory SSO in production" >&2
    exit 1
    ;;
esac

for url_key in KEYCLOAK_PUBLIC_URL FRAPPE_PUBLIC_URL NEFTEGAZ_REVIEW_PUBLIC_URL; do
  url_value="$(dotenv_value "$url_key")"
  [[ -z "$url_value" ]] && continue
  case "$url_value" in
    http://*|https://*) ;;
    *) echo "ERROR: $url_key must be an absolute HTTP(S) URL" >&2; exit 1 ;;
  esac
done

vault_image="$(dotenv_value VAULT_IMAGE)"
if [[ -n "$vault_image" && ! "$vault_image" =~ @sha256:[0-9a-fA-F]{64}$ ]]; then
  echo "ERROR: VAULT_IMAGE must be digest-pinned" >&2
  exit 1
fi

for template in \
  "$ROOT_DIR/docker/vault/runtime.env.tpl" \
  "$ROOT_DIR/docker/vault/keycloak.env.tpl" \
  "$ROOT_DIR/docker/vault/db-password.tpl" \
  "$ROOT_DIR/docker/vault/keycloak-db-password.tpl"; do
  [[ -s "$template" ]] || { echo "ERROR: missing Vault template: $template" >&2; exit 1; }
done

agent_config="$ROOT_DIR/docker/vault/agent.hcl"
[[ -s "$agent_config" ]] || { echo "ERROR: missing Vault Agent config: $agent_config" >&2; exit 1; }
for marker in \
  'method "approle"' \
  'role_id_file_path' \
  'secret_id_file_path' \
  'error_on_missing_key = true'; do
  grep -Fq "$marker" "$agent_config" || {
    echo "ERROR: Vault Agent config is missing required marker: $marker" >&2
    exit 1
  }
done

validate_fixture() {
  local fixture="$1"
  [[ -r "$fixture" ]] || { echo "ERROR: cannot read Vault fixture: $fixture" >&2; return 1; }
  python3 - "$fixture" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
try:
    payload = json.loads(path.read_text(encoding="utf-8"))
except (OSError, json.JSONDecodeError) as exc:
    print(f"ERROR: invalid Vault fixture: {exc}", file=sys.stderr)
    raise SystemExit(1)

if not isinstance(payload, dict):
    print("ERROR: Vault fixture must be a JSON object", file=sys.stderr)
    raise SystemExit(1)

vault = payload.get("vault") if isinstance(payload.get("vault"), dict) else payload
approle = payload.get("approle") if isinstance(payload.get("approle"), dict) else payload
render = payload.get("render") if isinstance(payload.get("render"), dict) else payload

status = str(payload.get("status") or vault.get("status") or "").strip().lower()
if status in {"sealed", "unavailable", "unauthorized", "missing", "incomplete"}:
    print(f"ERROR: Vault fixture state is fail-closed: {status}", file=sys.stderr)
    raise SystemExit(1)

for key, label in (
    ("available", "Vault unavailable"),
    ("reachable", "Vault unavailable"),
    ("initialized", "Vault is not initialized"),
    ("authorized", "AppRole unauthorized"),
):
    if key in vault and vault[key] is False:
        print(f"ERROR: {label}", file=sys.stderr)
        raise SystemExit(1)
    if key in approle and approle[key] is False:
        print(f"ERROR: {label}", file=sys.stderr)
        raise SystemExit(1)

if vault.get("sealed") is True or vault.get("unsealed") is False:
    print("ERROR: Vault is sealed", file=sys.stderr)
    raise SystemExit(1)

missing = []
for key in ("missing", "missing_path", "missing_paths", "missing_keys", "missing_key"):
    value = render.get(key, payload.get(key))
    if value:
        if isinstance(value, list):
            missing.extend(str(item) for item in value)
        else:
            missing.append(str(value))
if missing:
    print("ERROR: Vault render is missing required path or key", file=sys.stderr)
    raise SystemExit(1)

rendered = render.get("paths") or render.get("required_paths")
if isinstance(rendered, dict) and any(value is False for value in rendered.values()):
    print("ERROR: Vault render is incomplete", file=sys.stderr)
    raise SystemExit(1)

print("PASS: synthetic Vault preflight state is complete (values redacted)")
PY
}

if [[ -n "$FIXTURE_FILE" ]]; then
  validate_fixture "$FIXTURE_FILE"
fi

if [[ "$DRY_RUN" == "1" ]]; then
  echo "PASS: Vault contract is syntactically ready (dry-run; no Vault connection)"
  exit 0
fi

role_id_file="$(dotenv_value VAULT_ROLE_ID_FILE)"
secret_id_file="$(dotenv_value VAULT_SECRET_ID_FILE)"
root_dir_real="$(cd "$ROOT_DIR" && pwd -P)"
for path in "$role_id_file" "$secret_id_file"; do
  [[ "$path" = /* ]] || { echo "ERROR: AppRole file path must be absolute: $path" >&2; exit 1; }
  [[ -f "$path" && -s "$path" ]] || { echo "ERROR: AppRole file is missing or empty: $path" >&2; exit 1; }
  [[ ! -L "$path" ]] || { echo "ERROR: AppRole file must not be a symlink: $path" >&2; exit 1; }
  resolved="$(readlink -f -- "$path")"
  case "$resolved" in
    "$root_dir_real"|"$root_dir_real"/*)
      echo "ERROR: AppRole file must live outside the repository: $path" >&2
      exit 1
      ;;
  esac
  owner="$(stat -c '%u' -- "$path")"
  [[ "$owner" == "0" ]] || { echo "ERROR: AppRole file must be root-owned: $path" >&2; exit 1; }
  mode="$(stat -c '%a' "$path")"
  numeric_mode=$((8#$mode))
  if (( numeric_mode & 077 )); then
    echo "ERROR: AppRole file is readable or writable by group/others: $path" >&2
    exit 1
  fi
done

command -v docker >/dev/null 2>&1 || { echo "ERROR: docker is required for live Vault preflight" >&2; exit 1; }
compose=(docker compose --env-file "$ENV_FILE" -f "$ROOT_DIR/docker/compose.prod.yaml")
agent_check() {
  "${compose[@]}" exec -T vault-agent sh -ec '
  set -eu
  export VAULT_ADDR=http://vault:8200
  status="$(vault status -format=json 2>/dev/null || true)"
  printf "%s" "$status" | grep -Eq '"initialized"[[:space:]]*:[[:space:]]*true' || {
    echo "ERROR: Vault is unavailable or not initialized" >&2
    exit 1
  }
  printf "%s" "$status" | grep -Eq '"sealed"[[:space:]]*:[[:space:]]*false' || {
    echo "ERROR: Vault is sealed" >&2
    exit 1
  }
  token="$(vault write -field=token auth/approle/login \
    role_id="$(cat /vault/bootstrap/role-id)" \
    secret_id="$(cat /vault/bootstrap/secret-id)" 2>/dev/null)" || {
      echo "ERROR: AppRole is unauthorized" >&2
      exit 1
    }
  [ -n "$token" ] || { echo "ERROR: AppRole returned no token" >&2; exit 1; }
  data_file="$(mktemp)"
  trap "rm -f \"$data_file\"" EXIT
  if ! vault -token="$token" read -format=json elms/data/runtime >"$data_file" 2>/dev/null; then
    echo "ERROR: AppRole cannot read the required Vault path" >&2
    exit 1
  fi
  for key in DB_PASSWORD ADMIN_PASSWORD KEYCLOAK_CLIENT_SECRET ELMS_REVIEW_HANDOFF_SECRET \
    NEFTEGAZ_REVIEW_CLIENT_SECRET KEYCLOAK_DB_PASSWORD KEYCLOAK_ADMIN_PASSWORD \
    YANDEX_CLIENT_ID YANDEX_CLIENT_SECRET; do
    grep -q "\"$key\"" "$data_file" || {
      echo "ERROR: Vault path is missing a required key" >&2
      exit 1
    }
  done
  for file in \
    /run/elms-secrets/frappe/runtime.env \
    /run/elms-secrets/keycloak/runtime.env \
    /run/elms-secrets/db/db-password \
    /run/elms-secrets/db/keycloak-db-password; do
    test -s "$file" || { echo "ERROR: Vault Agent render is missing a required file" >&2; exit 1; }
  done
  grep -q "^DB_PASSWORD=" /run/elms-secrets/frappe/runtime.env || exit 1
  grep -q "^KEYCLOAK_CLIENT_SECRET=" /run/elms-secrets/frappe/runtime.env || exit 1
  grep -q "^KEYCLOAK_ADMIN_PASSWORD=" /run/elms-secrets/keycloak/runtime.env || exit 1
  grep -q "^YANDEX_CLIENT_ID=" /run/elms-secrets/keycloak/runtime.env || exit 1
  ' >/dev/null 2>&1
}

ready=0
for _ in $(seq 1 30); do
  if agent_check; then
    ready=1
    break
  fi
  sleep 2
done
if [[ "$ready" != "1" ]]; then
  echo "ERROR: Vault Agent authentication or required render is incomplete" >&2
  exit 1
fi

echo "PASS: Vault Agent is authenticated, authorized, and rendered the required files (values redacted)"
