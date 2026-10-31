#!/bin/sh
set -eu

if [ "${ELMS_VAULT_REQUIRED:-0}" = "1" ]; then
  VAULT_ENV_FILE="${ELMS_VAULT_ENV_FILE:-/run/elms-secrets/runtime.env}"
  if [ ! -s "$VAULT_ENV_FILE" ]; then
    echo "ERROR: required Vault render is missing: $VAULT_ENV_FILE" >&2
    exit 1
  fi
  # The render contains shell-quoted values and is mounted read-only.
  set -a
  # shellcheck disable=SC1090
  . "$VAULT_ENV_FILE"
  set +a
fi

if [ -n "${KEYCLOAK_DB_PASSWORD:-}" ]; then
  export KC_DB_PASSWORD="$KEYCLOAK_DB_PASSWORD"
fi

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
REVIEW_PUBLIC_URL="${NEFTEGAZ_REVIEW_PUBLIC_URL:-http://127.0.0.1:8765}"

case "$REVIEW_PUBLIC_URL" in
  http://*|https://*) ;;
  *)
    echo "ERROR: NEFTEGAZ_REVIEW_PUBLIC_URL must be an absolute HTTP(S) URL." >&2
    exit 1
    ;;
esac

case "$REVIEW_PUBLIC_URL" in
  *'|'*|*'&'*|*' '*|*'?'*|*'#'*|*$'\n'*|*$'\r'*)
    echo "ERROR: NEFTEGAZ_REVIEW_PUBLIC_URL contains unsupported characters." >&2
    exit 1
    ;;
esac

TEST_PASSWORD_COUNT=0
[ -n "${KEYCLOAK_TEST_ONE_PASSWORD:-}" ] && TEST_PASSWORD_COUNT=$((TEST_PASSWORD_COUNT + 1))
[ -n "${KEYCLOAK_TEST_TWO_PASSWORD:-}" ] && TEST_PASSWORD_COUNT=$((TEST_PASSWORD_COUNT + 1))
[ -n "${KEYCLOAK_TEST_ADMIN_PASSWORD:-}" ] && TEST_PASSWORD_COUNT=$((TEST_PASSWORD_COUNT + 1))

if [ "$TEST_PASSWORD_COUNT" -ne 0 ] && [ "$TEST_PASSWORD_COUNT" -ne 3 ]; then
  echo "ERROR: KEYCLOAK_TEST_*_PASSWORD must be provided for all three test accounts, or all left empty." >&2
  exit 1
fi

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
  RENDER_TEMPLATE="$TEMPLATE_FILE"
  if [ "$TEST_PASSWORD_COUNT" -eq 0 ]; then
    RENDER_TEMPLATE="${IMPORT_DIR}/realm-elms-no-test-accounts.json"
    sed \
      -e '/"username": "elms.test.one@elms.local"/,/^    }/ s/"enabled": true/"enabled": false/' \
      -e '/"username": "elms.test.two@elms.local"/,/^    }/ s/"enabled": true/"enabled": false/' \
      -e '/"username": "elms.test.admin@elms.local"/,/^    }/ s/"enabled": true/"enabled": false/' \
      "$TEMPLATE_FILE" > "$RENDER_TEMPLATE"
  fi
  if [ -n "$Y_ID" ] && [ -n "$Y_SEC" ]; then
    PUBLIC_URL_ESCAPED=$(printf '%s' "$REVIEW_PUBLIC_URL" | sed 's/[&|\\]/\\&/g')
    YANDEX_CLIENT_ID_ESCAPED=$(printf '%s' "$Y_ID" | sed 's/[&|\\]/\\&/g')
    YANDEX_CLIENT_SECRET_ESCAPED=$(printf '%s' "$Y_SEC" | sed 's/[&|\\]/\\&/g')
    KEYCLOAK_CLIENT_SECRET_ESCAPED=$(printf '%s' "${KEYCLOAK_CLIENT_SECRET:-}" | sed 's/[&|\\]/\\&/g')
    NEFTEGAZ_REVIEW_CLIENT_SECRET_ESCAPED=$(printf '%s' "${NEFTEGAZ_REVIEW_CLIENT_SECRET:-}" | sed 's/[&|\\]/\\&/g')
    KEYCLOAK_ADMIN_PASSWORD_ESCAPED=$(printf '%s' "${KEYCLOAK_ADMIN_PASSWORD:-}" | sed 's/[&|\\]/\\&/g')
    KEYCLOAK_TEST_ONE_PASSWORD_ESCAPED=$(printf '%s' "${KEYCLOAK_TEST_ONE_PASSWORD:-}" | sed 's/[&|\\]/\\&/g')
    KEYCLOAK_TEST_TWO_PASSWORD_ESCAPED=$(printf '%s' "${KEYCLOAK_TEST_TWO_PASSWORD:-}" | sed 's/[&|\\]/\\&/g')
    KEYCLOAK_TEST_ADMIN_PASSWORD_ESCAPED=$(printf '%s' "${KEYCLOAK_TEST_ADMIN_PASSWORD:-}" | sed 's/[&|\\]/\\&/g')
    sed -e "s|__NEFTEGAZ_REVIEW_PUBLIC_URL__|$PUBLIC_URL_ESCAPED|g" \
      -e "s|\${env.YANDEX_CLIENT_ID:}|$YANDEX_CLIENT_ID_ESCAPED|g" \
      -e "s|\${env.YANDEX_CLIENT_SECRET:}|$YANDEX_CLIENT_SECRET_ESCAPED|g" \
      -e "s|\${env.KEYCLOAK_CLIENT_SECRET:}|$KEYCLOAK_CLIENT_SECRET_ESCAPED|g" \
      -e "s|\${env.NEFTEGAZ_REVIEW_CLIENT_SECRET:}|$NEFTEGAZ_REVIEW_CLIENT_SECRET_ESCAPED|g" \
      -e "s|\${env.KEYCLOAK_ADMIN_PASSWORD}|$KEYCLOAK_ADMIN_PASSWORD_ESCAPED|g" \
      -e "s|\${env.KEYCLOAK_TEST_ONE_PASSWORD}|$KEYCLOAK_TEST_ONE_PASSWORD_ESCAPED|g" \
      -e "s|\${env.KEYCLOAK_TEST_TWO_PASSWORD}|$KEYCLOAK_TEST_TWO_PASSWORD_ESCAPED|g" \
      -e "s|\${env.KEYCLOAK_TEST_ADMIN_PASSWORD}|$KEYCLOAK_TEST_ADMIN_PASSWORD_ESCAPED|g" \
      -e '/"alias": "yandex"/,/}/s/"enabled": [a-z]*/"enabled": true/' "$RENDER_TEMPLATE" > "$OUTPUT_FILE"
  else
    PUBLIC_URL_ESCAPED=$(printf '%s' "$REVIEW_PUBLIC_URL" | sed 's/[&|\\]/\\&/g')
    YANDEX_CLIENT_ID_ESCAPED=$(printf '%s' "$Y_ID" | sed 's/[&|\\]/\\&/g')
    YANDEX_CLIENT_SECRET_ESCAPED=$(printf '%s' "$Y_SEC" | sed 's/[&|\\]/\\&/g')
    KEYCLOAK_CLIENT_SECRET_ESCAPED=$(printf '%s' "${KEYCLOAK_CLIENT_SECRET:-}" | sed 's/[&|\\]/\\&/g')
    NEFTEGAZ_REVIEW_CLIENT_SECRET_ESCAPED=$(printf '%s' "${NEFTEGAZ_REVIEW_CLIENT_SECRET:-}" | sed 's/[&|\\]/\\&/g')
    KEYCLOAK_ADMIN_PASSWORD_ESCAPED=$(printf '%s' "${KEYCLOAK_ADMIN_PASSWORD:-}" | sed 's/[&|\\]/\\&/g')
    KEYCLOAK_TEST_ONE_PASSWORD_ESCAPED=$(printf '%s' "${KEYCLOAK_TEST_ONE_PASSWORD:-}" | sed 's/[&|\\]/\\&/g')
    KEYCLOAK_TEST_TWO_PASSWORD_ESCAPED=$(printf '%s' "${KEYCLOAK_TEST_TWO_PASSWORD:-}" | sed 's/[&|\\]/\\&/g')
    KEYCLOAK_TEST_ADMIN_PASSWORD_ESCAPED=$(printf '%s' "${KEYCLOAK_TEST_ADMIN_PASSWORD:-}" | sed 's/[&|\\]/\\&/g')
    sed -e "s|__NEFTEGAZ_REVIEW_PUBLIC_URL__|$PUBLIC_URL_ESCAPED|g" \
      -e "s|\${env.YANDEX_CLIENT_ID:}|$YANDEX_CLIENT_ID_ESCAPED|g" \
      -e "s|\${env.YANDEX_CLIENT_SECRET:}|$YANDEX_CLIENT_SECRET_ESCAPED|g" \
      -e "s|\${env.KEYCLOAK_CLIENT_SECRET:}|$KEYCLOAK_CLIENT_SECRET_ESCAPED|g" \
      -e "s|\${env.NEFTEGAZ_REVIEW_CLIENT_SECRET:}|$NEFTEGAZ_REVIEW_CLIENT_SECRET_ESCAPED|g" \
      -e "s|\${env.KEYCLOAK_ADMIN_PASSWORD}|$KEYCLOAK_ADMIN_PASSWORD_ESCAPED|g" \
      -e "s|\${env.KEYCLOAK_TEST_ONE_PASSWORD}|$KEYCLOAK_TEST_ONE_PASSWORD_ESCAPED|g" \
      -e "s|\${env.KEYCLOAK_TEST_TWO_PASSWORD}|$KEYCLOAK_TEST_TWO_PASSWORD_ESCAPED|g" \
      -e "s|\${env.KEYCLOAK_TEST_ADMIN_PASSWORD}|$KEYCLOAK_TEST_ADMIN_PASSWORD_ESCAPED|g" \
      -e '/"alias": "yandex"/,/}/s/"enabled": [a-z]*/"enabled": false/' "$RENDER_TEMPLATE" > "$OUTPUT_FILE"
  fi
  [ "$RENDER_TEMPLATE" = "$TEMPLATE_FILE" ] || rm -f "$RENDER_TEMPLATE"
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
