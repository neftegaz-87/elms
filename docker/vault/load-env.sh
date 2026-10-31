#!/usr/bin/env bash
set -euo pipefail

if [[ "${ELMS_VAULT_REQUIRED:-1}" != "1" ]]; then
  return 0 2>/dev/null || exit 0
fi

env_file="${ELMS_VAULT_ENV_FILE:-/run/elms-secrets/runtime.env}"
if [[ ! -s "$env_file" ]]; then
  echo "ERROR: required Vault render is missing: $env_file" >&2
  exit 1
fi

set -a
# shellcheck disable=SC1090
source "$env_file"
set +a
