#!/bin/sh
set -eu

if [ "${KEYCLOAK_SEED_DEMO_USERS:-0}" != "1" ]; then
  echo "Keycloak demo-user seed is disabled."
  exit 0
fi

: "${KEYCLOAK_ADMIN:?KEYCLOAK_ADMIN is required}"
: "${KEYCLOAK_ADMIN_PASSWORD:?KEYCLOAK_ADMIN_PASSWORD is required}"

KCADM="${KCADM:-/opt/keycloak/bin/kcadm.sh}"
SERVER="${KEYCLOAK_SERVER:-http://127.0.0.1:8080}"
REALM="${KEYCLOAK_REALM:-elms}"
MAX_ATTEMPTS="${KEYCLOAK_SEED_MAX_ATTEMPTS:-90}"

if [ ! -x "$KCADM" ]; then
  echo "ERROR: kcadm.sh was not found at $KCADM" >&2
  exit 1
fi

test_password_count=0
[ -n "${KEYCLOAK_TEST_ONE_PASSWORD:-}" ] && test_password_count=$((test_password_count + 1))
[ -n "${KEYCLOAK_TEST_TWO_PASSWORD:-}" ] && test_password_count=$((test_password_count + 1))
[ -n "${KEYCLOAK_TEST_ADMIN_PASSWORD:-}" ] && test_password_count=$((test_password_count + 1))

if [ "$test_password_count" -eq 0 ]; then
  echo "Keycloak demo-user seed skipped: all KEYCLOAK_TEST_*_PASSWORD values are empty."
  exit 0
fi

if [ "$test_password_count" -ne 3 ]; then
  echo "ERROR: all three KEYCLOAK_TEST_*_PASSWORD values must be set together." >&2
  exit 1
fi

attempt=1
logged_in=0
while [ "$attempt" -le "$MAX_ATTEMPTS" ]; do
  if "$KCADM" config credentials \
    --server "$SERVER" \
    --realm master \
    --user "$KEYCLOAK_ADMIN" \
    --password "$KEYCLOAK_ADMIN_PASSWORD" >/dev/null 2>&1; then
    logged_in=1
    break
  fi
  sleep 2
  attempt=$((attempt + 1))
done

if [ "$logged_in" -ne 1 ]; then
  echo "ERROR: Keycloak did not become ready within $((MAX_ATTEMPTS * 2)) seconds." >&2
  exit 1
fi

attempt=1
realm_ready=0
while [ "$attempt" -le "$MAX_ATTEMPTS" ]; do
  if "$KCADM" get "realms/$REALM" >/dev/null 2>&1; then
    realm_ready=1
    break
  fi
  sleep 2
  attempt=$((attempt + 1))
done

if [ "$realm_ready" -ne 1 ]; then
  echo "ERROR: Keycloak realm '$REALM' did not become ready within $((MAX_ATTEMPTS * 2)) seconds." >&2
  exit 1
fi

find_user_id() {
  username="$1"
  "$KCADM" get users -r "$REALM" \
    -q "username=$username" \
    --fields id \
    --format csv \
    --noquotes 2>/dev/null | head -n 1 | tr -d '\r'
}

find_group_id() {
  group_name="$1"
  "$KCADM" get groups -r "$REALM" \
    -q "search=$group_name" \
    --fields id \
    --format csv \
    --noquotes 2>/dev/null | head -n 1 | tr -d '\r'
}

ensure_group() {
  group_name="$1"
  group_id="$(find_group_id "$group_name")"
  if [ -z "$group_id" ]; then
    "$KCADM" create groups -r "$REALM" -s "name=$group_name" >/dev/null
    group_id="$(find_group_id "$group_name")"
  fi
  if [ -z "$group_id" ]; then
    echo "ERROR: could not resolve Keycloak group '$group_name'." >&2
    exit 1
  fi
  printf '%s\n' "$group_id"
}

ensure_user() {
  username="$1"
  email="$2"
  password="$3"
  first_name="$4"
  last_name="$5"
  group_name="$6"
  realm_role="$7"

  user_id="$(find_user_id "$username")"
  if [ -z "$user_id" ]; then
    "$KCADM" create users -r "$REALM" \
      -s "username=$username" \
      -s "email=$email" \
      -s enabled=true \
      -s emailVerified=true \
      -s "firstName=$first_name" \
      -s "lastName=$last_name" >/dev/null
    user_id="$(find_user_id "$username")"
  else
    "$KCADM" update "users/$user_id" -r "$REALM" \
      -s "username=$username" \
      -s "email=$email" \
      -s enabled=true \
      -s emailVerified=true \
      -s "firstName=$first_name" \
      -s "lastName=$last_name" >/dev/null
  fi

  if [ -z "$user_id" ]; then
    echo "ERROR: could not resolve Keycloak user '$username'." >&2
    exit 1
  fi

  "$KCADM" set-password -r "$REALM" --userid "$user_id" --new-password "$password" >/dev/null
  group_id="$(ensure_group "$group_name")"
  "$KCADM" update "users/$user_id/groups/$group_id" -r "$REALM" -n >/dev/null
  "$KCADM" add-roles -r "$REALM" --uid "$user_id" --rolename "$realm_role" >/dev/null
  echo "Keycloak demo user synchronized: $username"
}

ensure_user \
  "admin" \
  "admin@elms.local" \
  "$KEYCLOAK_ADMIN_PASSWORD" \
  "Break-glass" \
  "Administrator" \
  "Administrators" \
  "admin"

ensure_user \
  "elms.test.one@elms.local" \
  "elms.test.one@elms.local" \
  "$KEYCLOAK_TEST_ONE_PASSWORD" \
  "ELMS Test" \
  "One" \
  "Employees" \
  "employee"

ensure_user \
  "elms.test.two@elms.local" \
  "elms.test.two@elms.local" \
  "$KEYCLOAK_TEST_TWO_PASSWORD" \
  "ELMS Test" \
  "Two" \
  "Employees" \
  "employee"

ensure_user \
  "elms.test.admin@elms.local" \
  "elms.test.admin@elms.local" \
  "$KEYCLOAK_TEST_ADMIN_PASSWORD" \
  "ELMS Test" \
  "Administrator" \
  "Administrators" \
  "admin"

echo "Keycloak demo-user seed complete."
