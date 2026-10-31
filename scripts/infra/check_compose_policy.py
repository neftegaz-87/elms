#!/usr/bin/env python3
"""Validate the ELMS production Compose boundary.

This deliberately validates the canonical file, not an arbitrary merged
Compose project.  The canonical production graph must be safe to consume on a
host that only has release images and operator-managed secret files.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover - an operator-facing message
    raise SystemExit("PyYAML is required to run the Compose policy check") from exc


EXPECTED_SERVICES = {
    "vault",
    "vault-agent",
    "db",
    "redis-cache",
    "redis-queue",
    "configurator",
    "create-site",
    "backend",
    "websocket",
    "queue-short",
    "queue-long",
    "scheduler",
    "frontend",
    "keycloak-db",
    "keycloak",
    "caddy",
}

HEALTH_REQUIRED = {
    "vault",
    "vault-agent",
    "db",
    "redis-cache",
    "redis-queue",
    "backend",
    "frontend",
    "keycloak-db",
    "keycloak",
    "caddy",
}

ONE_SHOT_SERVICES = {"configurator", "create-site"}
ALLOWED_RELATIVE_MOUNTS = ("./vault/", "./caddy/")
PLACEHOLDER_IMAGES = {"latest", "dev", "prod-local"}


def _load(path: Path) -> dict[str, Any]:
    try:
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise SystemExit(f"cannot read {path}: {exc}") from exc
    if not isinstance(document, dict):
        raise SystemExit(f"{path} is not a YAML mapping")
    return document


def _iter_strings(value: Any):
    if isinstance(value, dict):
        for key, item in value.items():
            yield str(key)
            yield from _iter_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _iter_strings(item)
    elif value is not None:
        yield str(value)


def _image_has_forbidden_tag(image: str) -> bool:
    # Registry ports contain colons, so inspect only the part after the final
    # slash. Digest-pinned refs are accepted even when their tag is transitional.
    if "@sha256:" in image:
        return False
    tail = image.rsplit("/", 1)[-1]
    tag = tail.rsplit(":", 1)[-1] if ":" in tail else ""
    return tag in PLACEHOLDER_IMAGES or tag == ""


def validate(document: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    services = document.get("services")
    if not isinstance(services, dict):
        return ["top-level services mapping is required"]

    missing = sorted(EXPECTED_SERVICES - set(services))
    unexpected = sorted(set(services) - EXPECTED_SERVICES)
    if missing:
        errors.append(f"missing production services: {', '.join(missing)}")
    if unexpected:
        errors.append(f"unexpected production services: {', '.join(unexpected)}")

    networks = document.get("networks", {})
    if not isinstance(networks, dict) or networks.get("private", {}).get("internal") is not True:
        errors.append("private network must be declared internal")

    for name, raw_service in services.items():
        if not isinstance(raw_service, dict):
            errors.append(f"service {name} must be a mapping")
            continue
        service = raw_service

        if "build" in service:
            errors.append(f"{name}: build is forbidden in canonical production Compose")
        image = service.get("image")
        if not image:
            errors.append(f"{name}: image is required")
        elif _image_has_forbidden_tag(str(image)):
            # A variable expression is allowed to resolve to a release digest;
            # explicit mutable defaults are not.
            if "CUSTOM_IMAGE_REF" not in str(image) and "KEYCLOAK_IMAGE_REF" not in str(image):
                errors.append(f"{name}: mutable or missing image tag: {image}")
        if "ports" in service:
            errors.append(f"{name}: host ports belong only to an explicit edge/staged overlay")
        if service.get("network_mode") == "host":
            errors.append(f"{name}: host networking is forbidden")

        if name not in ONE_SHOT_SERVICES and not service.get("restart"):
            errors.append(f"{name}: restart policy is required")
        security = service.get("security_opt", [])
        if "no-new-privileges:true" not in security and name not in ONE_SHOT_SERVICES:
            errors.append(f"{name}: no-new-privileges:true is required")
        limits = service.get("deploy", {}).get("resources", {}).get("limits", {})
        if name not in ONE_SHOT_SERVICES and (not isinstance(limits, dict) or not limits):
            errors.append(f"{name}: bounded deploy.resources.limits are required")
        if name in HEALTH_REQUIRED and not service.get("healthcheck"):
            errors.append(f"{name}: healthcheck is required")

        for item in service.get("volumes", []) or []:
            if isinstance(item, str):
                source = item.split(":", 1)[0]
                if source.startswith("../") or source in {".", ".."}:
                    errors.append(f"{name}: source checkout mount is forbidden: {item}")
                if source.startswith("./") and not source.startswith(ALLOWED_RELATIVE_MOUNTS):
                    errors.append(f"{name}: unexpected relative host mount: {item}")

    # The integration secret must arrive through Vault Agent, never through a
    # plain Compose environment value or a source checkout mount.
    flattened = "\n".join(_iter_strings(document))
    if "ELMS_REVIEW_HANDOFF_SECRET" in flattened:
        errors.append("ELMS_REVIEW_HANDOFF_SECRET must not be present in Compose YAML")
    if re.search(r"(?m)^\s*[- ]*\.?\.?/elms(?::|/)", flattened):
        errors.append("source application mounts are forbidden in canonical production Compose")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", type=Path, default=Path("docker/compose.prod.yaml"))
    args = parser.parse_args()
    errors = validate(_load(args.file))
    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print(f"PASS: production Compose policy ({args.file})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
