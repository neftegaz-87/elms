#!/usr/bin/env python3
"""Allowlisted server-side ELMS release/deploy/rollback wrapper.

The wrapper is intended to live outside the checkout on the production host.
It accepts a validated release manifest and executes only the fixed Compose
operation for this project.  It never runs arbitrary shell text and never
removes state volumes.
"""

from __future__ import annotations

import argparse
import fcntl
import json
import os
import shutil
import subprocess
import sys
from contextlib import contextmanager, nullcontext
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from check_release_manifest import load, validate  # noqa: E402


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    root.add_argument("--root", type=Path, default=Path("/opt/elms"), help="server-side release root")
    root.add_argument("--compose-file", type=Path, default=None)
    root.add_argument("--env-file", type=Path, default=None)
    sub = root.add_subparsers(dest="command", required=True)

    deploy = sub.add_parser("deploy")
    deploy.add_argument("--manifest", type=Path, required=True)
    deploy.add_argument("--approved", action="store_true")
    deploy.add_argument("--execute", action="store_true")

    rollback = sub.add_parser("rollback")
    rollback.add_argument("--manifest", type=Path, required=True)
    rollback.add_argument("--approved", action="store_true")
    rollback.add_argument("--execute", action="store_true")

    status = sub.add_parser("status")
    status.add_argument("--json", action="store_true")
    return root


@contextmanager
def lock(root: Path):
    lock_path = root / "deploy.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        yield
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def manifest_path(path: Path) -> Path:
    resolved = path.expanduser().resolve()
    if not resolved.is_file():
        raise SystemExit(f"ERROR: release manifest does not exist: {resolved}")
    errors = validate(load(resolved))
    if errors:
        raise SystemExit("ERROR: release manifest failed validation: " + "; ".join(errors))
    return resolved


def compose_command(args: argparse.Namespace) -> list[str]:
    root = args.root.resolve()
    compose_file = (args.compose_file or root / "docker/compose.prod.yaml").resolve()
    env_file = (args.env_file or root / "docker/.env.prod").resolve()
    if not compose_file.is_file() or not env_file.is_file():
        raise SystemExit("ERROR: production Compose or env file is missing")
    return ["docker", "compose", "--env-file", str(env_file), "-f", str(compose_file)]


def release_environment(data: dict) -> dict[str, str]:
    """Return only non-secret image overrides for Compose interpolation."""
    environment = os.environ.copy()
    for image in data.get("images", []):
        name = image.get("name")
        if name == "elms":
            key = "CUSTOM_IMAGE_REF"
        elif name == "elms-keycloak":
            key = "KEYCLOAK_IMAGE_REF"
        else:
            continue
        environment[key] = f"{image['ref']}@{image['digest']}"
    return environment


def required_evidence(root: Path) -> list[Path]:
    return [
        Path(os.environ.get("ELMS_BACKUP_EVIDENCE", root / "evidence/backup-fresh.json")),
        Path(os.environ.get("ELMS_VAULT_EVIDENCE", root / "evidence/vault-preflight.ok")),
    ]


def run_release(args: argparse.Namespace, action: str) -> dict:
    manifest = manifest_path(args.manifest)
    data = load(manifest)
    root = args.root.resolve()
    releases = root / "releases"
    release_id = str(data["commit"])
    stored = releases / f"{release_id}.json"
    compose = compose_command(args)
    environment = release_environment(data)

    if action == "rollback":
        current = root / "current.json"
        if not current.is_file():
            raise SystemExit("ERROR: rollback requires a recorded current release")
        current_data = load(current)
        if current_data.get("commit") == release_id:
            raise SystemExit("ERROR: rollback target is already the current release")
        if releases not in manifest.parents:
            raise SystemExit("ERROR: rollback manifest must come from the verified releases directory")

    # The wrapper never accepts arbitrary compose arguments. The only executing
    # sequence is config -> pull -> wait-for-health -> internal smoke.
    commands = [compose + ["config", "--quiet"]]
    if args.execute:
        if not args.approved:
            raise SystemExit("ERROR: --approved is required for an executing release action")
        missing = [str(path) for path in required_evidence(root) if not path.is_file()]
        if missing:
            raise SystemExit("ERROR: required Vault/backup evidence is missing")
        commands.extend(
            (
                compose + ["pull"],
                compose + ["up", "-d", "--remove-orphans", "--wait", "--wait-timeout", "600"],
                compose + ["exec", "-T", "backend", "curl", "--fail", "--silent", "--output", "/dev/null", "http://127.0.0.1:8000/login"],
                compose + ["exec", "-T", "frontend", "curl", "--fail", "--silent", "--output", "/dev/null", "http://127.0.0.1:8080/login"],
                compose + ["exec", "-T", "keycloak", "curl", "--fail", "--silent", "--output", "/dev/null", "http://127.0.0.1:8080/health/ready"],
            )
        )

    lock_context = lock(root) if args.execute else nullcontext()
    with lock_context:
        if args.execute:
            releases.mkdir(parents=True, exist_ok=True)
        for command in commands:
            subprocess.run(command, check=True, env=environment)
        if args.execute:
            shutil.copyfile(manifest, stored)
            current = root / "current.json"
            temporary = root / ".current.json.tmp"
            temporary.unlink(missing_ok=True)
            temporary.symlink_to(stored)
            temporary.replace(current)

    result = {"action": action, "release": release_id, "executed": bool(args.execute)}
    print(json.dumps(result, sort_keys=True))
    return result


def status(args: argparse.Namespace) -> int:
    current = args.root.resolve() / "current.json"
    value = {"current": str(current), "present": current.is_file()}
    if current.is_file():
        data = load(current)
        value["commit"] = data.get("commit")
        value["images"] = [item.get("name") for item in data.get("images", []) if isinstance(item, dict)]
    print(json.dumps(value, sort_keys=True) if args.json else " ".join(f"{k}={v}" for k, v in value.items()))
    return 0


def main() -> int:
    args = parser().parse_args()
    if args.command == "status":
        return status(args)
    run_release(args, args.command)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
