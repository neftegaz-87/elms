#!/bin/sh
set -eu

TEMPLATE_FILE="${KEYCLOAK_REALM_TEMPLATE:-/opt/keycloak/data/import-template/realm-elms.json}"
if [ ! -f "$TEMPLATE_FILE" ] && [ -f "docker/keycloak/realm-elms.json" ]; then
  TEMPLATE_FILE="docker/keycloak/realm-elms.json"
fi

DEFAULT_IMPORT_DIR="/opt/keycloak/data/import"
if [ ! -d "/opt/keycloak" ]; then
  DEFAULT_IMPORT_DIR="/tmp/keycloak-import"
fi
IMPORT_DIR="${KEYCLOAK_IMPORT_DIR:-$DEFAULT_IMPORT_DIR}"
OUTPUT_FILE="${IMPORT_DIR}/realm-elms.json"

Y_ID="${YANDEX_CLIENT_ID:-}"
Y_SEC="${YANDEX_CLIENT_SECRET:-}"

# Check Yandex credentials branches:
# 1. Both empty: disables broker
# 2. Partial (exactly one set): bootstrap fails with exit 1
# 3. Both present: enables broker
if [ -n "$Y_ID" ] && [ -z "$Y_SEC" ]; then
  echo "ERROR: Partial Yandex credentials. Both YANDEX_CLIENT_ID and YANDEX_CLIENT_SECRET must be provided, or both left empty." >&2
  exit 1
fi

if [ -z "$Y_ID" ] && [ -n "$Y_SEC" ]; then
  echo "ERROR: Partial Yandex credentials. Both YANDEX_CLIENT_ID and YANDEX_CLIENT_SECRET must be provided, or both left empty." >&2
  exit 1
fi

if [ -f "$TEMPLATE_FILE" ]; then
  mkdir -p "$IMPORT_DIR"
  if [ -n "$Y_ID" ] && [ -n "$Y_SEC" ]; then
    sed '/"alias": "yandex"/,/}/s/"enabled": [a-z]*/"enabled": true/' "$TEMPLATE_FILE" > "$OUTPUT_FILE"
  else
    sed '/"alias": "yandex"/,/}/s/"enabled": [a-z]*/"enabled": false/' "$TEMPLATE_FILE" > "$OUTPUT_FILE"
  fi
fi

if [ "${1:-}" = "--dry-run" ] || [ "${DRY_RUN:-0}" = "1" ]; then
  echo "Keycloak entrypoint realm preparation complete."
  exit 0
fi

if [ -x "/opt/keycloak/bin/kc.sh" ]; then
  if [ "$#" -gt 0 ]; then
    exec /opt/keycloak/bin/kc.sh "$@"
  else
    exec /opt/keycloak/bin/kc.sh start-dev --import-realm
  fi
elif [ "$#" -gt 0 ]; then
  exec "$@"
fi
