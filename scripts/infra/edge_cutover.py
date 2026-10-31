#!/usr/bin/env python3
"""Preflight and explicitly gated Caddy edge operations for ELMS."""

from __future__ import annotations

import argparse
import fcntl
import json
import os
import socket
import subprocess
import sys
import time
from contextlib import contextmanager
from pathlib import Path


def port_state(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex((host, port)) == 0


def root_path(args: argparse.Namespace) -> Path:
    return args.root.resolve()


def evidence_is_fresh(path: Path, max_age_hours: int) -> None:
    if not path.is_file():
        raise SystemExit("ERROR: predecessor edge evidence file is missing")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit("ERROR: predecessor edge evidence must be JSON") from exc
    required = {
        "release": "passed",
        "vault": "passed",
        "backup": "fresh",
        "staged": "passed",
        "rollback": "passed",
    }
    for key, expected in required.items():
        if not isinstance(value.get(key), dict) or value[key].get("status") != expected:
            raise SystemExit(f"ERROR: predecessor evidence is missing a passing {key} gate")
    if value.get("owner_approved") is not True:
        raise SystemExit("ERROR: predecessor evidence does not record owner approval")
    age_seconds = max(0.0, time.time() - path.stat().st_mtime)
    if age_seconds > max_age_hours * 3600:
        raise SystemExit("ERROR: predecessor edge evidence is stale")


@contextmanager
def cutover_lock(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        yield
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def preflight(args: argparse.Namespace) -> int:
    root = root_path(args)
    compose = root / "docker/compose.prod.yaml"
    staged = root / "docker/compose.prod.staged.yaml"
    caddy = root / "docker/caddy/Caddyfile"
    staged_caddy = root / "docker/caddy/Caddyfile.staged"
    errors: list[str] = []
    for path in (compose, staged, caddy, staged_caddy):
        if not path.is_file():
            errors.append(f"missing edge artifact: {path}")
    if compose.is_file() and "ports:" in compose.read_text(encoding="utf-8"):
        errors.append("canonical Compose must not own public ports")
    if staged_caddy.is_file() and "127.0.0.1" not in staged.read_text(encoding="utf-8"):
        errors.append("staged edge must bind localhost only")
    if caddy.is_file() and "/healthz" not in caddy.read_text(encoding="utf-8"):
        errors.append("public Caddyfile must define /healthz")
    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print("PASS: staged edge artifacts and public-port ownership boundary")
    return 0


def status(args: argparse.Namespace) -> int:
    value = {
        "http_80_in_use": port_state(80),
        "https_443_in_use": port_state(443),
        "staged_18080_in_use": port_state(18080),
        "note": "port ownership is evidence only; no process was changed",
    }
    print(json.dumps(value, sort_keys=True))
    return 0


def execute(args: argparse.Namespace, action: str) -> int:
    if not args.approved or not args.execute:
        raise SystemExit(f"ERROR: {action} requires both --approved and --execute")
    if args.max_age_hours <= 0:
        raise SystemExit("ERROR: --max-age-hours must be positive")
    evidence = args.predecessor_evidence
    if not evidence:
        raise SystemExit("ERROR: predecessor edge evidence file is required")
    evidence_is_fresh(evidence.resolve(), args.max_age_hours)

    root = root_path(args)
    env_file = args.env_file.resolve()
    compose = [
        "docker",
        "compose",
        "--env-file",
        str(env_file),
        "-f",
        str(root / "docker/compose.prod.yaml"),
        "-f",
        str(root / "docker/compose.prod.edge.yaml"),
    ]
    lock_path = Path(os.environ.get("ELMS_EDGE_LOCK", "/run/lock/elms-edge-cutover.lock"))
    with cutover_lock(lock_path):
        if action == "switch":
            if port_state(80) or port_state(443):
                raise SystemExit("ERROR: 80/443 are still occupied; host edge must be released explicitly")
            subprocess.run(compose + ["up", "-d", "--remove-orphans", "--wait", "caddy"], check=True)
            if not port_state(80) or not port_state(443):
                raise SystemExit("ERROR: container Caddy did not acquire both public ports")
        else:
            subprocess.run(compose + ["stop", "caddy"], check=True)
            subprocess.run(["systemctl", "start", "caddy"], check=True)
            subprocess.run(["systemctl", "is-active", "--quiet", "caddy"], check=True)
    print(json.dumps({"action": action, "executed": True}, sort_keys=True))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--env-file", type=Path, default=Path("docker/.env.prod"))
    sub = parser.add_subparsers(dest="command", required=True)
    staged = sub.add_parser("preflight")
    staged.add_argument("--staged", action="store_true")
    sub.add_parser("status")
    for name in ("switch", "rollback"):
        action = sub.add_parser(name)
        action.add_argument("--approved", action="store_true")
        action.add_argument("--execute", action="store_true")
        action.add_argument("--predecessor-evidence", type=Path)
        action.add_argument("--max-age-hours", type=int, default=24)
    args = parser.parse_args()
    if args.command == "preflight":
        return preflight(args)
    if args.command == "status":
        return status(args)
    return execute(args, args.command)


if __name__ == "__main__":
    raise SystemExit(main())
