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
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from contextlib import contextmanager, nullcontext
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from backup_runner import read_success_evidence
from check_release_manifest import load, validate

TARGET_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.@:\-]*$")
UNSAFE_TARGETS = frozenset(
    {
        "localhost",
        "127.0.0.1",
        "::1",
        "elms.localhost",
        "elms-dev",
        "dev",
        "development",
    }
)
REQUIRED_IMAGE_NAMES = frozenset({"elms", "elms-keycloak"})


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    root.add_argument("--root", type=Path, default=None, help="explicit server-side release root")
    root.add_argument(
        "--target",
        default=None,
        help="explicit SSH target recorded by the protected workflow (deploy/rollback only)",
    )
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


def validate_target(target: str | None) -> str:
    """Reject implicit/local targets before a state-changing release action."""
    value = str(target or "").strip()
    if not value:
        raise SystemExit("ERROR: an explicit --target is required for deploy and rollback")
    if not TARGET_PATTERN.fullmatch(value):
        raise SystemExit("ERROR: --target contains unsupported shell or path characters")

    host = value.rsplit("@", 1)[-1].lower()
    if host in UNSAFE_TARGETS:
        raise SystemExit("ERROR: --target must not resolve to a local or development target")
    if host.startswith(("dev.", "elms-dev.")):
        raise SystemExit("ERROR: --target must not resolve to a development target")
    return value


def explicit_root(args: argparse.Namespace, *, state_changing: bool) -> Path:
    if args.root is None:
        if state_changing:
            raise SystemExit("ERROR: an explicit --root is required for deploy and rollback")
        return Path("/opt/elms").resolve()
    root = args.root.expanduser().resolve()
    if root == Path("/"):
        raise SystemExit("ERROR: --root must not be the filesystem root")
    return root


def fixed_path(root: Path, supplied: Path | None, relative: str) -> Path:
    expected = (root / relative).resolve()
    candidate = expected if supplied is None else supplied.expanduser().resolve()
    if candidate != expected:
        raise SystemExit(f"ERROR: only the fixed production {relative} is allowed")
    if not candidate.is_file():
        raise SystemExit(f"ERROR: production file is missing: {candidate}")
    return candidate


def compose_command(args: argparse.Namespace) -> list[str]:
    root = explicit_root(args, state_changing=True)
    compose_file = fixed_path(root, args.compose_file, "docker/compose.prod.yaml")
    env_file = fixed_path(root, args.env_file, "docker/.env.prod")
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
    def resolve(value: str | Path) -> Path:
        path = Path(value)
        return path if path.is_absolute() else root / path

    backup_value = os.environ.get("ELMS_BACKUP_EVIDENCE")
    vault_value = os.environ.get("ELMS_VAULT_EVIDENCE")
    if not backup_value or not vault_value:
        raise SystemExit("ERROR: ELMS_BACKUP_EVIDENCE and ELMS_VAULT_EVIDENCE are required")
    return [
        resolve(backup_value),
        resolve(vault_value),
    ]


def validate_vault_evidence(path: Path) -> None:
    try:
        value = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise SystemExit(f"ERROR: invalid Vault preflight evidence: {path}") from exc
    if value.strip() != "PASS":
        raise SystemExit(f"ERROR: Vault preflight evidence is not verified: {path}")


def validate_required_evidence(root: Path, max_age_hours: int = 24) -> None:
    backup_evidence, vault_evidence = required_evidence(root)
    read_success_evidence(backup_evidence, max_age_hours)
    validate_vault_evidence(vault_evidence)


def validate_compose_binding(data: dict, compose_file: Path) -> None:
    actual = "sha256:" + hashlib.sha256(compose_file.read_bytes()).hexdigest()
    if data.get("compose_sha256") != actual:
        raise SystemExit("ERROR: release manifest is bound to a different production Compose file")


def verified_release_data(path: Path, releases: Path) -> dict:
    resolved = path.expanduser().resolve()
    if resolved.parent != releases.resolve():
        raise SystemExit("ERROR: verified release must be a direct member of the releases directory")
    errors = validate(load(resolved))
    if errors:
        raise SystemExit("ERROR: recorded release failed validation: " + "; ".join(errors))
    return load(resolved)


def record_release(manifest: Path, data: dict, releases: Path) -> None:
    releases.mkdir(parents=True, exist_ok=True)
    stored = releases / f"{data['commit']}.json"
    if stored.exists():
        existing = verified_release_data(stored, releases)
        if existing != data:
            raise SystemExit("ERROR: immutable release record already contains different content")
    else:
        shutil.copyfile(manifest, stored)

    current = releases.parent / "current.json"
    temporary = releases.parent / ".current.json.tmp"
    temporary.unlink(missing_ok=True)
    temporary.symlink_to(stored)
    temporary.replace(current)


def run_release(args: argparse.Namespace, action: str) -> dict:
    validate_target(args.target)
    manifest = manifest_path(args.manifest)
    data = load(manifest)
    root = explicit_root(args, state_changing=True)
    releases = root / "releases"
    release_id = str(data["commit"])
    compose = compose_command(args)
    compose_file = Path(compose[compose.index("-f") + 1])
    validate_compose_binding(data, compose_file)
    environment = release_environment(data)

    if action == "rollback":
        current = root / "current.json"
        if not current.is_file():
            raise SystemExit("ERROR: rollback requires a recorded current release")
        current_data = verified_release_data(current, releases)
        if current_data.get("commit") == release_id:
            raise SystemExit("ERROR: rollback target is already the current release")
        if manifest.parent != releases.resolve():
            raise SystemExit("ERROR: rollback manifest must come from the verified releases directory")

    # The wrapper never accepts arbitrary compose arguments. The only executing
    # sequence is config -> pull -> wait-for-health -> internal smoke.
    commands = [compose + ["config", "--quiet"]]
    if args.execute:
        if not args.approved:
            raise SystemExit("ERROR: --approved is required for an executing release action")
        validate_required_evidence(root)
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
            record_release(manifest, data, releases)

    result = {"action": action, "release": release_id, "executed": bool(args.execute)}
    print(json.dumps(result, sort_keys=True))
    return result


def status(args: argparse.Namespace) -> int:
    root = explicit_root(args, state_changing=False)
    current = root / "current.json"
    value = {"current": str(current), "present": current.is_file()}
    if current.is_file():
        data = verified_release_data(current, root / "releases")
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
