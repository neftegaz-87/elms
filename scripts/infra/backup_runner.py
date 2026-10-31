#!/usr/bin/env python3
"""Safe ELMS backup and restore-preflight helper.

The runner intentionally operates on an operator-provided export directory.
It does not inspect or copy live Docker volumes implicitly, and it never
removes a volume or prunes a repository.  A production scheduler can export
the named volumes/database dumps into the staging directory and then invoke
the encrypted restic backup command.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
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


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def manifest() -> dict:
    return {
        "schema": "elms-backup-manifest/v1",
        "application": "elms",
        "generated_at": now(),
        "policy": {
            "rpo_hours": 24,
            "rto_hours": 4,
            "encrypted_off_host_repository": True,
            "retention_days": 30,
            "minimum_free_bytes": int(os.environ.get("BACKUP_MIN_FREE_BYTES", "10737418240")),
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
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"ERROR: invalid backup manifest: {path}") from exc
    expected = {item[0] for item in STATE_ITEMS}
    actual = {item.get("name") for item in value.get("items", []) if isinstance(item, dict)}
    if value.get("schema") != "elms-backup-manifest/v1" or actual != expected:
        raise SystemExit("ERROR: backup manifest does not cover the complete ELMS state inventory")
    if value.get("policy", {}).get("encrypted_off_host_repository") is not True:
        raise SystemExit("ERROR: backup manifest does not require encrypted off-host storage")


def ensure_capacity(path: Path) -> None:
    usage = shutil.disk_usage(path)
    minimum = int(os.environ.get("BACKUP_MIN_FREE_BYTES", "10737418240"))
    if usage.free < minimum:
        raise SystemExit(f"ERROR: backup target has insufficient free space ({usage.free} bytes)")


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
    result = subprocess.run(["restic", *arguments], env=env, check=False)
    if result.returncode:
        raise SystemExit(f"ERROR: restic command failed with exit {result.returncode}")


def report(path: Path, max_age_hours: int) -> None:
    if not path.is_file():
        raise SystemExit(f"ERROR: backup success evidence is missing: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        completed = datetime.fromisoformat(str(value["completed_at"]).replace("Z", "+00:00"))
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise SystemExit(f"ERROR: invalid backup success evidence: {path}") from exc
    if datetime.now(timezone.utc) - completed > timedelta(hours=max_age_hours):
        raise SystemExit(f"ERROR: latest verified backup is older than {max_age_hours} hours")
    print(json.dumps({"status": "fresh", "completed_at": value["completed_at"], "max_age_hours": max_age_hours}))


def restore_preflight(target: Path) -> None:
    resolved = target.expanduser().resolve()
    active_markers = (
        Path("/var/lib/docker/volumes").resolve(),
        Path("/var/lib/docker/volumes/elms-prod_").resolve(),
    )
    if resolved == Path("/") or resolved == Path.cwd().resolve():
        raise SystemExit("ERROR: restore target is too broad")
    if any(str(resolved).startswith(str(marker)) for marker in active_markers):
        raise SystemExit("ERROR: restore target may not be an active Docker volume path")
    if "elms-prod" in resolved.parts:
        raise SystemExit("ERROR: restore target looks like the active production project")
    resolved.mkdir(parents=True, exist_ok=True)
    ensure_capacity(resolved)
    marker = resolved / ".elms-disposable-restore"
    marker.write_text("This directory is a disposable restore target.\n", encoding="utf-8")
    print(f"PASS: disposable restore target is safe: {resolved}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    manifest_parser = subparsers.add_parser("manifest")
    manifest_parser.add_argument("--output", type=Path, required=True)

    restore_parser = subparsers.add_parser("restore-preflight")
    restore_parser.add_argument("--target", type=Path, required=True)

    backup_parser = subparsers.add_parser("backup")
    backup_parser.add_argument("--source-root", type=Path, required=True)
    backup_parser.add_argument("--manifest", type=Path, required=True)
    backup_parser.add_argument("--status-output", type=Path)

    verify_parser = subparsers.add_parser("verify")
    verify_parser.add_argument("--read-data", action="store_true", help="run restic check --read-data")

    report_parser = subparsers.add_parser("report")
    report_parser.add_argument("--last-success", type=Path, required=True)
    report_parser.add_argument("--max-age-hours", type=int, default=24)

    args = parser.parse_args()
    if args.command == "manifest":
        write_manifest(args.output)
    elif args.command == "restore-preflight":
        restore_preflight(args.target)
    elif args.command == "backup":
        source = args.source_root.resolve()
        if not source.is_dir():
            raise SystemExit(f"ERROR: backup source directory does not exist: {source}")
        ensure_capacity(source)
        if not args.manifest.is_file():
            raise SystemExit(f"ERROR: backup manifest does not exist: {args.manifest}")
        validate_manifest_file(args.manifest)
        run_restic(["backup", str(source), "--tag", "elms", "--tag", "manifest-v1"])
        if args.status_output:
            args.status_output.parent.mkdir(parents=True, exist_ok=True)
            args.status_output.write_text(
                json.dumps({"status": "verified-upload", "completed_at": now()}) + "\n",
                encoding="utf-8",
            )
        print("PASS: encrypted restic backup completed")
    elif args.command == "verify":
        run_restic(["check", "--read-data"] if args.read_data else ["check"])
        print("PASS: restic repository verification completed")
    elif args.command == "report":
        if args.max_age_hours <= 0:
            raise SystemExit("ERROR: --max-age-hours must be positive")
        report(args.last_success, args.max_age_hours)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
