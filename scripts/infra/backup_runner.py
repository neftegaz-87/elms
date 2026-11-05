#!/usr/bin/env python3
"""Safe ELMS backup and restore-preflight helper.

The runner intentionally operates on an operator-provided export directory.
It does not inspect or copy live Docker volumes implicitly, and it never
removes a volume or performs repository retention deletion.  A production
scheduler can export the named volumes/database dumps into the staging directory
and then invoke
the encrypted restic backup command.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path


STATE_ITEMS = (
    ("frappe-sites", "sites", "application files and uploads", "consistent-filesystem-snapshot"),
    ("frappe-logs", "logs", "diagnostic logs", "filesystem-snapshot"),
    ("mariadb", "db-data", "Frappe database state", "mariadb-logical-dump"),
    ("keycloak-postgres", "keycloak-db-data", "identity database state", "postgres-logical-dump"),
    ("redis-queue", "redis-queue-data", "durable background queue state", "redis-consistent-checkpoint"),
    ("vault-raft", "vault-data", "Vault Raft state and recovery metadata", "vault-raft-snapshot"),
    ("caddy-data", "caddy-data", "ACME certificates and edge state", "filesystem-snapshot"),
    ("caddy-config", "caddy-config", "Caddy persisted configuration", "filesystem-snapshot"),
)

MANIFEST_ITEM_FIELDS = {
    "name",
    "volume",
    "description",
    "restore_method",
    "owner",
    "review_service_state",
}

SENSITIVE_MANIFEST_MARKERS = (
    "elms_review_handoff_secret",
    "secret_id",
    "oauth_cookie",
    "unseal_key",
    "recovery_key",
    "private_key",
)
STATUS_SCHEMA = "elms-backup-status/v1"
DISPOSABLE_MARKER = ".elms-disposable-restore"
DISPOSABLE_MARKER_SCHEMA = "elms-disposable-restore-target/v1"
RESTORE_REHEARSAL_SCHEMA = "elms-restore-rehearsal/v1"
RESTORE_REHEARSAL_SENSITIVE_MARKERS = (
    "password",
    "token",
    "client_secret",
    "secret_id",
    "oauth_cookie",
    "unseal_key",
    "recovery_key",
    "private_key",
)
RESTORE_SMOKE_CHECKS = (
    ("MariaDB", "db-data", "logical dump import and schema smoke"),
    ("Keycloak PostgreSQL", "keycloak-db-data", "logical dump import and identity discovery smoke"),
    ("Vault Raft", "vault-data", "synthetic snapshot restore and redacted health smoke"),
    ("Caddy data/config", "caddy-data,caddy-config", "configuration and persisted edge-state smoke"),
)


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def minimum_free_bytes() -> int:
    raw = os.environ.get("BACKUP_MIN_FREE_BYTES", "10737418240")
    try:
        value = int(raw)
    except ValueError as exc:
        raise SystemExit("ERROR: BACKUP_MIN_FREE_BYTES must be an integer") from exc
    if value <= 0:
        raise SystemExit("ERROR: BACKUP_MIN_FREE_BYTES must be positive")
    return value


def manifest() -> dict:
    return {
        "schema": "elms-backup-manifest/v1",
        "application": "elms",
        "generated_at": now(),
        "policy": {
            "capacity_gate": "hard",
            "client_side_encryption": True,
            "rpo_hours": 24,
            "rto_hours": 4,
            "encrypted_off_host_repository": True,
            "retention_days": 30,
            "minimum_free_bytes": minimum_free_bytes(),
            "repository": "restic-s3-compatible",
        },
        "redaction": {
            "logs_and_status": "status-only",
            "excluded_material": ["pii", "oauth", "vault-recovery"],
        },
        "items": [
            {
                "name": name,
                "volume": volume,
                "description": description,
                "restore_method": restore_method,
                "owner": "elms",
                "review_service_state": False,
            }
            for name, volume, description, restore_method in STATE_ITEMS
        ],
        "excluded": [
            "review-service application state (owned by its repository)",
            "Vault tokens, AppRole secret IDs and unseal/recovery values",
            "OAuth session cookies and transient Redis cache",
        ],
    }


def write_manifest(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"PASS: wrote non-secret backup manifest to {path}")


def validate_manifest_file(path: Path) -> None:
    try:
        raw = path.read_text(encoding="utf-8")
        lowered = raw.lower()
        for marker in SENSITIVE_MANIFEST_MARKERS:
            if marker in lowered:
                raise SystemExit(f"ERROR: secret-like manifest field is forbidden: {marker}")
        value = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"ERROR: invalid backup manifest: {path}") from exc
    if not isinstance(value, dict) or value.get("application") != "elms":
        raise SystemExit("ERROR: backup manifest application must be elms")
    expected = {item[0] for item in STATE_ITEMS}
    items = value.get("items")
    actual = {item.get("name") for item in items if isinstance(item, dict)} if isinstance(items, list) else set()
    if value.get("schema") != "elms-backup-manifest/v1" or actual != expected:
        raise SystemExit("ERROR: backup manifest does not cover the complete ELMS state inventory")
    policy = value.get("policy")
    if not isinstance(policy, dict):
        raise SystemExit("ERROR: backup manifest policy is required")
    if (
        policy.get("capacity_gate") != "hard"
        or policy.get("client_side_encryption") is not True
        or policy.get("encrypted_off_host_repository") is not True
        or policy.get("repository") != "restic-s3-compatible"
        or policy.get("rpo_hours") != 24
        or policy.get("rto_hours") != 4
        or policy.get("retention_days") != 30
        or not isinstance(policy.get("minimum_free_bytes"), int)
        or policy["minimum_free_bytes"] <= 0
    ):
        raise SystemExit("ERROR: backup manifest policy is incomplete or unsafe")
    if value.get("redaction") != {
        "logs_and_status": "status-only",
        "excluded_material": ["pii", "oauth", "vault-recovery"],
    }:
        raise SystemExit("ERROR: backup manifest redaction policy is incomplete")
    expected_items = {item[0]: item for item in STATE_ITEMS}
    for item in items:
        if not isinstance(item, dict) or set(item) != MANIFEST_ITEM_FIELDS:
            raise SystemExit("ERROR: backup manifest contains unexpected or incomplete item fields")
        expected_item = expected_items[item["name"]]
        if (
            item.get("volume") != expected_item[1]
            or item.get("description") != expected_item[2]
            or item.get("restore_method") != expected_item[3]
            or item.get("owner") != "elms"
            or item.get("review_service_state") is not False
        ):
            raise SystemExit("ERROR: backup manifest state item is incomplete or unsafe")


def ensure_capacity(path: Path) -> None:
    paths = [path]
    configured = os.environ.get("BACKUP_CAPACITY_PATH", "").strip()
    if configured:
        paths.append(Path(configured).expanduser())
    minimum = minimum_free_bytes()
    for candidate in paths:
        resolved = candidate.resolve()
        if not resolved.is_dir():
            raise SystemExit(f"ERROR: backup capacity path does not exist: {resolved}")
        usage = shutil.disk_usage(resolved)
        if usage.free < minimum:
            raise SystemExit(f"ERROR: backup target has insufficient free space ({usage.free} bytes)")


def _capacity_probe(path: Path) -> Path:
    candidate = path
    while not candidate.exists():
        parent = candidate.parent
        if parent == candidate:
            raise SystemExit(f"ERROR: backup capacity path has no existing parent: {path}")
        candidate = parent
    if not candidate.is_dir():
        raise SystemExit(f"ERROR: backup capacity path is not a directory: {candidate}")
    return candidate.resolve()


def ensure_restore_capacity(path: Path) -> None:
    paths = [_capacity_probe(path)]
    configured = os.environ.get("BACKUP_CAPACITY_PATH", "").strip()
    if configured:
        configured_path = Path(configured).expanduser().resolve()
        if not configured_path.is_dir():
            raise SystemExit(f"ERROR: backup capacity path does not exist: {configured_path}")
        paths.append(configured_path)
    minimum = minimum_free_bytes()
    for candidate in paths:
        usage = shutil.disk_usage(candidate)
        if usage.free < minimum:
            raise SystemExit(f"ERROR: backup target has insufficient free space ({usage.free} bytes)")


def _has_symlink_component(path: Path) -> bool:
    lexical = Path(os.path.abspath(os.path.expanduser(str(path))))
    current = Path(lexical.anchor)
    for part in lexical.parts[1:]:
        current /= part
        try:
            if current.is_symlink():
                return True
        except OSError as exc:
            raise SystemExit(f"ERROR: cannot inspect restore target path: {current}") from exc
        if not current.exists():
            break
    return False


def _is_below(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _validate_disposable_marker(path: Path) -> None:
    if not path.is_file():
        raise SystemExit("ERROR: existing restore target requires a disposable marker")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError) as exc:
        raise SystemExit("ERROR: existing restore target has an invalid disposable marker") from exc
    if value != {
        "schema": DISPOSABLE_MARKER_SCHEMA,
        "status": "ready",
        "target_policy": "disposable-only",
    }:
        raise SystemExit("ERROR: existing restore target marker is not a disposable target contract")


def _write_disposable_marker(target: Path) -> None:
    marker = target / DISPOSABLE_MARKER
    try:
        marker.write_text(
            json.dumps(
                {
                    "schema": DISPOSABLE_MARKER_SCHEMA,
                    "status": "ready",
                    "target_policy": "disposable-only",
                },
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        os.chmod(marker, 0o600)
    except OSError as exc:
        raise SystemExit(f"ERROR: cannot write disposable restore marker: {marker}") from exc


def restore_rehearsal_manifest() -> dict:
    return {
        "schema": RESTORE_REHEARSAL_SCHEMA,
        "application": "elms",
        "rpo_hours": 24,
        "rto_hours": 4,
        "target_policy": {
            "disposable_only": True,
            "active_project": "elms-prod",
            "active_volume_write": False,
            "destructive_cleanup": False,
        },
        "redaction": {
            "logs_and_status": "status-only",
            "excluded_material": ["pii", "oauth", "vault-recovery"],
        },
        "order": [
            "restore-preflight",
            "MariaDB",
            "Keycloak PostgreSQL",
            "Vault Raft",
            "Caddy data/config",
            "redacted owner evidence",
        ],
        "smoke_checks": [
            {"name": name, "state": state, "check": check, "evidence": "redacted-status"}
            for name, state, check in RESTORE_SMOKE_CHECKS
        ],
        "excluded": [
            "review-service application state",
            "live credentials and recovery material",
        ],
    }


def validate_restore_rehearsal_manifest(value: object) -> None:
    if not isinstance(value, dict):
        raise SystemExit("ERROR: restore rehearsal manifest must be an object")
    lowered = json.dumps(value, sort_keys=True).lower()
    for marker in RESTORE_REHEARSAL_SENSITIVE_MARKERS:
        if marker in lowered:
            raise SystemExit(f"ERROR: secret-like rehearsal field is forbidden: {marker}")
    expected = restore_rehearsal_manifest()
    if value != expected:
        raise SystemExit("ERROR: restore rehearsal manifest contract is incomplete or unsafe")


def write_restore_rehearsal_manifest(path: Path) -> None:
    value = restore_rehearsal_manifest()
    validate_restore_rehearsal_manifest(value)
    path = path.expanduser().resolve()
    if path == Path("/"):
        raise SystemExit("ERROR: restore rehearsal manifest path is unsafe")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.chmod(path, 0o600)
    except OSError as exc:
        raise SystemExit(f"ERROR: cannot write restore rehearsal manifest: {path}") from exc
    print(f"PASS: wrote redacted restore rehearsal manifest to {path}")


def restic_env() -> tuple[str, str]:
    repository = os.environ.get("RESTIC_REPOSITORY", "")
    password_file = os.environ.get("RESTIC_PASSWORD_FILE", "")
    if not repository or not password_file:
        raise SystemExit("ERROR: RESTIC_REPOSITORY and RESTIC_PASSWORD_FILE are required")
    password_path = Path(password_file)
    if not password_path.is_file() or not password_path.stat().st_size:
        raise SystemExit("ERROR: RESTIC_PASSWORD_FILE is missing or empty")
    if password_path.stat().st_mode & 0o077:
        raise SystemExit("ERROR: RESTIC_PASSWORD_FILE must not be group/world readable")
    return repository, password_file


def run_restic(arguments: list[str]) -> None:
    repository, password_file = restic_env()
    env = os.environ.copy()
    env["RESTIC_REPOSITORY"] = repository
    env["RESTIC_PASSWORD_FILE"] = password_file
    try:
        result = subprocess.run(["restic", *arguments], env=env, check=False)
    except OSError as exc:
        raise SystemExit("ERROR: restic executable is unavailable") from exc
    if result.returncode:
        raise SystemExit(f"ERROR: restic command failed with exit {result.returncode}")


def write_status(path: Path, status: str, **values: str) -> None:
    path = path.expanduser().resolve()
    if path == Path("/"):
        raise SystemExit("ERROR: backup status path is unsafe")
    path.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, str] = {
        "schema": STATUS_SCHEMA,
        "status": status,
        "updated_at": now(),
    }
    payload.update(values)
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary_name = handle.name
            handle.write(json.dumps(payload, sort_keys=True) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary_name, 0o600)
        os.replace(temporary_name, path)
    except OSError as exc:
        if temporary_name:
            Path(temporary_name).unlink(missing_ok=True)
        raise SystemExit(f"ERROR: cannot write backup status evidence: {path}") from exc


def parse_status_timestamp(value: object, path: Path) -> datetime:
    if not path.is_file():
        raise SystemExit(f"ERROR: backup success evidence is missing: {path}")
    try:
        completed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise SystemExit(f"ERROR: invalid backup success timestamp: {path}") from exc
    if completed.tzinfo is None:
        raise SystemExit(f"ERROR: backup success timestamp must include timezone: {path}")
    return completed.astimezone(timezone.utc)


def read_success_evidence(path: Path, max_age_hours: int) -> dict:
    if max_age_hours <= 0:
        raise SystemExit("ERROR: --max-age-hours must be positive")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError) as exc:
        raise SystemExit(f"ERROR: invalid backup success evidence: {path}") from exc
    if not isinstance(value, dict):
        raise SystemExit(f"ERROR: invalid backup success evidence: {path}")
    if (
        value.get("schema") != STATUS_SCHEMA
        or value.get("status") != "verified"
        or value.get("upload") != "restic-backup"
        or value.get("verification") != "restic-check"
    ):
        raise SystemExit(f"ERROR: backup success evidence is not verified: {path}")
    completed = parse_status_timestamp(value.get("completed_at"), path)
    current = datetime.now(timezone.utc)
    if completed > current + timedelta(minutes=5):
        raise SystemExit(f"ERROR: backup success evidence is from the future: {path}")
    if current - completed > timedelta(hours=max_age_hours):
        raise SystemExit(f"ERROR: latest verified backup is older than {max_age_hours} hours")
    return value


def report(path: Path, max_age_hours: int) -> None:
    value = read_success_evidence(path, max_age_hours)
    print(json.dumps({"status": "fresh", "completed_at": value["completed_at"], "max_age_hours": max_age_hours}))


def require_upload_status(path: Path) -> None:
    if not path.is_file():
        raise SystemExit(f"ERROR: backup upload evidence is missing: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError) as exc:
        raise SystemExit(f"ERROR: invalid backup upload evidence: {path}") from exc
    if not isinstance(value, dict) or value.get("schema") != STATUS_SCHEMA or value.get("status") != "running":
        raise SystemExit(f"ERROR: backup upload evidence is not pending verification: {path}")


def restore_preflight(target: Path) -> None:
    lexical = Path(os.path.abspath(os.path.expanduser(str(target))))
    active_volume_root = (Path("/var/lib") / "docker" / "volumes").resolve(strict=False)
    try:
        resolved = lexical.resolve(strict=False)
    except (OSError, RuntimeError) as exc:
        raise SystemExit("ERROR: restore target cannot be resolved safely") from exc
    if _is_below(lexical, active_volume_root) or _is_below(resolved, active_volume_root):
        raise SystemExit("ERROR: restore target may not be an active Docker volume path")
    if "elms-prod" in lexical.parts or "elms-prod" in resolved.parts:
        raise SystemExit("ERROR: restore target looks like the active production project")
    if _has_symlink_component(lexical):
        raise SystemExit("ERROR: restore target may not contain symlink components")
    if resolved == Path("/") or resolved == Path.cwd().resolve():
        raise SystemExit("ERROR: restore target is too broad")
    target_exists = lexical.exists()
    if target_exists and not lexical.is_dir():
        raise SystemExit("ERROR: restore target must be a directory")
    ensure_restore_capacity(resolved)
    if target_exists:
        _validate_disposable_marker(resolved / DISPOSABLE_MARKER)
    else:
        try:
            resolved.mkdir(parents=True, exist_ok=False, mode=0o700)
        except OSError as exc:
            raise SystemExit(f"ERROR: cannot create disposable restore target: {resolved}") from exc
        _write_disposable_marker(resolved)
    print(f"PASS: disposable restore target is safe: {resolved}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    manifest_parser = subparsers.add_parser("manifest")
    manifest_parser.add_argument("--output", type=Path, required=True)

    restore_parser = subparsers.add_parser("restore-preflight")
    restore_parser.add_argument("--target", type=Path, required=True)

    rehearsal_parser = subparsers.add_parser(
        "restore-rehearsal-manifest", aliases=["restore-manifest"]
    )
    rehearsal_parser.add_argument("--output", type=Path, required=True)

    backup_parser = subparsers.add_parser("backup")
    backup_parser.add_argument("--source-root", type=Path, required=True)
    backup_parser.add_argument("--manifest", type=Path, required=True)
    backup_parser.add_argument("--status-output", type=Path)

    verify_parser = subparsers.add_parser("verify")
    verify_parser.add_argument("--read-data", action="store_true", help="run restic check --read-data")
    verify_parser.add_argument("--status-output", type=Path)

    report_parser = subparsers.add_parser("report")
    report_parser.add_argument("--last-success", type=Path, required=True)
    report_parser.add_argument("--max-age-hours", type=int, default=24)

    args = parser.parse_args()
    if args.command == "manifest":
        write_manifest(args.output)
    elif args.command == "restore-preflight":
        restore_preflight(args.target)
    elif args.command in {"restore-rehearsal-manifest", "restore-manifest"}:
        write_restore_rehearsal_manifest(args.output)
    elif args.command == "backup":
        source = args.source_root.resolve()
        if not source.is_dir():
            raise SystemExit(f"ERROR: backup source directory does not exist: {source}")
        ensure_capacity(source)
        if not args.manifest.is_file():
            raise SystemExit(f"ERROR: backup manifest does not exist: {args.manifest}")
        validate_manifest_file(args.manifest)
        if args.status_output:
            write_status(args.status_output, "running", operation="backup")
        try:
            run_restic(["backup", str(source), "--tag", "elms", "--tag", "manifest-v1"])
        except SystemExit:
            if args.status_output:
                write_status(args.status_output, "failed", operation="backup")
            raise
    elif args.command == "verify":
        if args.status_output:
            require_upload_status(args.status_output)
            write_status(args.status_output, "verifying", operation="verify")
        try:
            run_restic(["check", "--read-data"] if args.read_data else ["check"])
        except SystemExit:
            if args.status_output:
                write_status(args.status_output, "failed", operation="verify")
            raise
        if args.status_output:
            write_status(
                args.status_output,
                "verified",
                upload="restic-backup",
                verification="restic-check",
                completed_at=now(),
            )
        print("PASS: restic repository verification completed")
    elif args.command == "report":
        if args.max_age_hours <= 0:
            raise SystemExit("ERROR: --max-age-hours must be positive")
        report(args.last_success, args.max_age_hours)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
