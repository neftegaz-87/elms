#!/usr/bin/env python3
"""Validate a non-secret, digest-pinned ELMS release manifest."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")
COMMIT = re.compile(r"^[0-9a-f]{7,64}$")
FORBIDDEN = re.compile(r"(?i)(password|secret|token|private.?key|unseal|recovery)")
MUTABLE_TAGS = {"latest", "dev", "prod-local"}


def load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"ERROR: invalid release manifest {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise SystemExit("ERROR: release manifest must be a JSON object")
    return value


def walk_keys(value: Any, prefix: str = ""):
    if isinstance(value, dict):
        for key, item in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            yield path, str(key)
            yield from walk_keys(item, path)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from walk_keys(item, f"{prefix}[{index}]")


def image_tag(ref: str) -> str:
    without_digest = ref.split("@", 1)[0]
    tail = without_digest.rsplit("/", 1)[-1]
    return tail.rsplit(":", 1)[-1] if ":" in tail else ""


def validate(value: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if value.get("schema") != "elms-release-manifest/v1":
        errors.append("schema must be elms-release-manifest/v1")
    commit = value.get("commit")
    if not isinstance(commit, str) or not COMMIT.fullmatch(commit):
        errors.append("commit must be a hexadecimal commit id")
    if not isinstance(value.get("compose_sha256"), str) or not SHA256.fullmatch(value["compose_sha256"]):
        errors.append("compose_sha256 must be a sha256 digest")
    images = value.get("images")
    if not isinstance(images, list) or not images:
        errors.append("images must be a non-empty list")
    else:
        names: set[str] = set()
        for index, image in enumerate(images):
            if not isinstance(image, dict):
                errors.append(f"images[{index}] must be an object")
                continue
            name = image.get("name")
            ref = image.get("ref")
            digest = image.get("digest")
            if not isinstance(name, str) or not name:
                errors.append(f"images[{index}].name is required")
            elif name in names:
                errors.append(f"duplicate image name: {name}")
            else:
                names.add(name)
            if not isinstance(ref, str) or not ref:
                errors.append(f"images[{index}].ref is required")
            else:
                tag = image_tag(ref)
                if not tag:
                    errors.append(f"images[{index}].ref must include a release tag")
                elif tag in MUTABLE_TAGS:
                    errors.append(f"images[{index}].ref must use an immutable release tag, not {tag}")
            if not isinstance(digest, str) or not SHA256.fullmatch(digest):
                errors.append(f"images[{index}].digest must be sha256")
    smoke = value.get("smoke")
    if not isinstance(smoke, dict) or smoke.get("status") != "passed":
        errors.append("smoke.status must be passed")
    if value.get("rollback_verified") is not True:
        errors.append("rollback_verified must be true")

    for path, key in walk_keys(value):
        if FORBIDDEN.search(key):
            errors.append(f"secret-like key is forbidden in release manifest: {path}")
    serialized = json.dumps(value, ensure_ascii=False)
    if FORBIDDEN.search(serialized):
        # The key check above is precise; this second check catches accidental
        # secret labels embedded in free-form metadata.
        errors.append("secret-like content is forbidden in release manifest")
    return sorted(set(errors))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", "--fixture", dest="manifest", type=Path, required=True)
    args = parser.parse_args()
    errors = validate(load(args.manifest))
    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print(f"PASS: release manifest ({args.manifest})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
