#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ENV_FILE="$ROOT_DIR/docker/.env.prod"
ACTION="snapshot"
OUTPUT=""
INPUT=""
TARGET=""
PROJECT_NAME=""
FIXTURE_FILE=""
SYNTHETIC=0

usage() {
  cat <<'EOF'
Usage:
  vault_snapshot.sh snapshot --output PATH [--env-file PATH]
  vault_snapshot.sh restore --input PATH --target PATH --fixture

Snapshot streams an authenticated Vault Raft snapshot to a protected file.
Restore rehearses a synthetic snapshot into a disposable directory; real
restore is reserved for an explicitly named disposable Compose project.

Options:
  --output PATH             snapshot destination
  --input PATH              snapshot source for restore
  --target PATH             disposable restore target for fixture restore
  --project-name NAME       disposable Compose project for real restore
  --env-file PATH           production metadata dotenv file
  --fixture [PATH]           synthetic snapshot input, or synthetic restore mode

The operator credential is supplied as ELMS_VAULT_OPERATOR_TOKEN. Snapshot
contents and credentials are never printed.
EOF
}

if [[ "${1:-}" == "snapshot" || "${1:-}" == "restore" ]]; then
  ACTION="$1"
  shift
fi

while [[ $# -gt 0 ]]; do
  case "$1" in
    --output)
      [[ $# -ge 2 ]] || { echo "ERROR: --output needs a path" >&2; exit 2; }
      OUTPUT="$2"
      shift 2
      ;;
    --input)
      [[ $# -ge 2 ]] || { echo "ERROR: --input needs a path" >&2; exit 2; }
      INPUT="$2"
      shift 2
      ;;
    --target)
      [[ $# -ge 2 ]] || { echo "ERROR: --target needs a path" >&2; exit 2; }
      TARGET="$2"
      shift 2
      ;;
    --project-name)
      [[ $# -ge 2 ]] || { echo "ERROR: --project-name needs a name" >&2; exit 2; }
      PROJECT_NAME="$2"
      shift 2
      ;;
    --env-file)
      [[ $# -ge 2 ]] || { echo "ERROR: --env-file needs a path" >&2; exit 2; }
      ENV_FILE="$2"
      shift 2
      ;;
    --fixture)
      if [[ $# -ge 2 && "$2" != -* ]]; then
        FIXTURE_FILE="$2"
        shift 2
      else
        SYNTHETIC=1
        shift
      fi
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

write_snapshot() {
  local destination="$1"
  local temporary
  [[ -n "$destination" ]] || { echo "ERROR: --output is required" >&2; exit 2; }
  output_path="$(readlink -m -- "$destination")"
  [[ "$output_path" != "/" ]] || { echo "ERROR: snapshot output is unsafe" >&2; exit 1; }
  [[ ! -e "$output_path" ]] || {
    echo "ERROR: snapshot output already exists; choose a new protected path" >&2
    exit 1
  }
  install -d -m 700 "$(dirname "$output_path")"
  temporary="$(mktemp "${output_path}.partial.XXXXXX")"
  trap 'rm -f -- "$temporary"' RETURN
  chmod 600 "$temporary"
  cat > "$temporary"
  [[ -s "$temporary" ]] || { echo "ERROR: snapshot is empty" >&2; exit 1; }
  mv -- "$temporary" "$output_path"
  chmod 600 "$output_path"
  trap - RETURN
  echo "PASS: Vault Raft snapshot written to protected path (values redacted)"
}

synthetic_snapshot() {
  [[ -r "$FIXTURE_FILE" ]] || { echo "ERROR: synthetic snapshot fixture is required" >&2; exit 1; }
  python3 - "$FIXTURE_FILE" <<'PY' | write_snapshot "$OUTPUT"
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
try:
    payload = json.loads(path.read_text(encoding="utf-8"))
except (OSError, json.JSONDecodeError) as exc:
    print(f"ERROR: invalid synthetic snapshot fixture: {exc}", file=sys.stderr)
    raise SystemExit(1)

if not isinstance(payload, dict) or payload.get("schema") != "elms-vault-synthetic-snapshot/v1":
    print("ERROR: unsupported synthetic snapshot fixture", file=sys.stderr)
    raise SystemExit(1)
if not isinstance(payload.get("secrets"), dict) or not payload["secrets"]:
    print("ERROR: synthetic snapshot fixture has no secret-key contract", file=sys.stderr)
    raise SystemExit(1)

print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
PY
}

synthetic_restore() {
  [[ -n "$INPUT" && -r "$INPUT" ]] || { echo "ERROR: --input is required for fixture restore" >&2; exit 1; }
  [[ -n "$TARGET" ]] || { echo "ERROR: --target is required for fixture restore" >&2; exit 1; }
  python3 - "$INPUT" "$TARGET" <<'PY'
import hashlib
import json
import sys
from pathlib import Path

source = Path(sys.argv[1])
target = Path(sys.argv[2]).resolve()
if target == Path("/") or str(target).startswith("/var/lib/docker/volumes/"):
    print("ERROR: restore target is not disposable", file=sys.stderr)
    raise SystemExit(1)
try:
    payload = json.loads(source.read_text(encoding="utf-8"))
except (OSError, json.JSONDecodeError) as exc:
    print(f"ERROR: invalid synthetic snapshot: {exc}", file=sys.stderr)
    raise SystemExit(1)
if not isinstance(payload, dict) or payload.get("schema") != "elms-vault-synthetic-snapshot/v1":
    print("ERROR: restore accepts only the synthetic snapshot schema in fixture mode", file=sys.stderr)
    raise SystemExit(1)
secrets = payload.get("secrets")
if not isinstance(secrets, dict) or not all(isinstance(key, str) for key in secrets):
    print("ERROR: synthetic snapshot secret-key contract is invalid", file=sys.stderr)
    raise SystemExit(1)
target.mkdir(mode=0o700, parents=True, exist_ok=True)
marker = {
    "schema": "elms-vault-disposable-restore/v1",
    "status": "restored",
    "snapshot_id": str(payload.get("snapshot_id", "synthetic")),
    "secret_keys": sorted(secrets),
    "fixture_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
}
(target / ".elms-disposable-restore").write_text(
    json.dumps(marker, ensure_ascii=False, sort_keys=True) + "\n",
    encoding="utf-8",
)
print("PASS: synthetic snapshot restored into disposable target (values redacted)")
PY
}

real_snapshot() {
  [[ -r "$ENV_FILE" ]] || { echo "ERROR: cannot read $ENV_FILE" >&2; exit 1; }
  [[ -n "${ELMS_VAULT_OPERATOR_TOKEN:-}" ]] || {
    echo "ERROR: operator credential must be supplied by the operator environment" >&2
    exit 1
  }
  command -v docker >/dev/null 2>&1 || { echo "ERROR: docker is required" >&2; exit 1; }
  compose=(docker compose --env-file "$ENV_FILE" -f "$ROOT_DIR/docker/compose.prod.yaml")
  "${compose[@]}" exec -T -e ELMS_VAULT_OPERATOR_TOKEN vault sh -ec \
    'vault -token="$ELMS_VAULT_OPERATOR_TOKEN" operator raft snapshot save /tmp/elms-raft.snap >/dev/null && cat /tmp/elms-raft.snap' \
    | write_snapshot "$OUTPUT"
}

real_restore() {
  [[ -r "$ENV_FILE" ]] || { echo "ERROR: cannot read $ENV_FILE" >&2; exit 1; }
  [[ -n "$INPUT" && -r "$INPUT" ]] || { echo "ERROR: --input is required" >&2; exit 1; }
  [[ "$PROJECT_NAME" == elms-vault-restore-* ]] || {
    echo "ERROR: real restore requires a disposable project named elms-vault-restore-*" >&2
    exit 1
  }
  [[ -n "${ELMS_VAULT_OPERATOR_TOKEN:-}" ]] || {
    echo "ERROR: operator credential must be supplied by the operator environment" >&2
    exit 1
  }
  command -v docker >/dev/null 2>&1 || { echo "ERROR: docker is required" >&2; exit 1; }
  compose=(docker compose --project-name "$PROJECT_NAME" --env-file "$ENV_FILE" -f "$ROOT_DIR/docker/compose.prod.yaml")
  "${compose[@]}" exec -T -e ELMS_VAULT_OPERATOR_TOKEN vault sh -ec \
    'cat > /tmp/elms-raft.restore && vault -token="$ELMS_VAULT_OPERATOR_TOKEN" operator raft snapshot restore -force /tmp/elms-raft.restore' \
    < "$INPUT" >/dev/null
  echo "PASS: Vault snapshot restored into disposable Compose project (values redacted)"
}

if [[ "$ACTION" == "snapshot" ]]; then
  if [[ -n "$FIXTURE_FILE" ]]; then
    synthetic_snapshot
  else
    real_snapshot
  fi
elif [[ "$ACTION" == "restore" ]]; then
  if [[ "$SYNTHETIC" == "1" ]]; then
    synthetic_restore
  else
    real_restore
  fi
else
  echo "ERROR: unsupported action: $ACTION" >&2
  exit 2
fi
