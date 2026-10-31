#!/usr/bin/env bash
set -euo pipefail

source /usr/local/bin/load-elms-vault-env.sh

if [[ "${1:-}" == "--new-site" ]]; then
  [[ "$#" -eq 2 ]] || { echo "ERROR: --new-site requires exactly one site name" >&2; exit 2; }
  [[ -n "${ADMIN_PASSWORD:-}" && -n "${DB_PASSWORD:-}" ]] || {
    echo "ERROR: Vault render is missing the site bootstrap contract" >&2
    exit 1
  }
  exec bench new-site \
    --mariadb-user-host-login-scope=% \
    --admin-password="$ADMIN_PASSWORD" \
    --db-root-username=root \
    --db-root-password="$DB_PASSWORD" \
    --no-mariadb-socket \
    --set-default "$2"
fi

exec "$@"
