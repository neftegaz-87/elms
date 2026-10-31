#!/usr/bin/env python3
"""Check that production credentials are delivered only through Vault Agent."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML is required to run the secret contract check") from exc


REQUIRED_KEYS = {
    "DB_PASSWORD",
    "ADMIN_PASSWORD",
    "KEYCLOAK_DB_PASSWORD",
    "KEYCLOAK_ADMIN_PASSWORD",
    "KEYCLOAK_CLIENT_SECRET",
    "NEFTEGAZ_REVIEW_CLIENT_SECRET",
    "ELMS_REVIEW_HANDOFF_SECRET",
    "YANDEX_CLIENT_ID",
    "YANDEX_CLIENT_SECRET",
}

TEMPLATE_KEYS = {
    "runtime.env.tpl": {
        "DB_PASSWORD",
        "ADMIN_PASSWORD",
        "KEYCLOAK_CLIENT_SECRET",
        "ELMS_REVIEW_HANDOFF_SECRET",
        "NEFTEGAZ_REVIEW_CLIENT_SECRET",
    },
    "keycloak.env.tpl": {
        "KEYCLOAK_DB_PASSWORD",
        "KEYCLOAK_ADMIN_PASSWORD",
        "KEYCLOAK_CLIENT_SECRET",
        "NEFTEGAZ_REVIEW_CLIENT_SECRET",
        "YANDEX_CLIENT_ID",
        "YANDEX_CLIENT_SECRET",
    },
}

FORBIDDEN_DIRECT_KEYS = REQUIRED_KEYS


def _load_yaml(path: Path) -> dict[str, Any]:
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise SystemExit(f"{path} is not a YAML mapping")
    return document


def _environment_items(value: Any):
    if isinstance(value, dict):
        yield from value.items()
    elif isinstance(value, list):
        for item in value:
            if isinstance(item, str) and "=" in item:
                yield item.split("=", 1)


def validate(compose_path: Path, vault_dir: Path) -> list[str]:
    document = _load_yaml(compose_path)
    services = document.get("services", {})
    errors: list[str] = []

    agent = services.get("vault-agent", {})
    agent_config = vault_dir / "agent.hcl"
    agent_text = compose_path.read_text(encoding="utf-8")
    if agent_config.is_file():
        agent_text += "\n" + agent_config.read_text(encoding="utf-8")
    else:
        errors.append(f"missing Vault Agent config: {agent_config}")
    for marker in ("runtime.env.tpl", "keycloak.env.tpl", "db-password.tpl", "keycloak-db-password.tpl", "/vault/bootstrap/role-id", "/vault/bootstrap/secret-id", "vault-runtime"):
        if marker not in agent_text:
            errors.append(f"vault-agent contract is missing {marker}")
    if agent_text.count("error_on_missing_key = true") < 4:
        errors.append("every Vault Agent template must fail closed on a missing key")
    if not agent.get("healthcheck"):
        errors.append("vault-agent must have a render readiness healthcheck")
    for marker in ("method \"approle\"", "role_id_file_path", "secret_id_file_path", "exit_on_retry_failure = true"):
        if marker not in agent_config.read_text(encoding="utf-8"):
            errors.append(f"Vault Agent config is missing {marker}")

    expected_render_paths = {
        "create-site": "/run/elms-secrets/frappe/runtime.env",
        "backend": "/run/elms-secrets/frappe/runtime.env",
        "keycloak": "/run/elms-secrets/keycloak/runtime.env",
    }
    for service_name, expected_path in expected_render_paths.items():
        service = services.get(service_name, {})
        environment = service.get("environment", {}) if isinstance(service, dict) else {}
        actual_path = environment.get("ELMS_VAULT_ENV_FILE") if isinstance(environment, dict) else None
        if actual_path != expected_path:
            errors.append(
                f"{service_name}: ELMS_VAULT_ENV_FILE must point to {expected_path}"
            )

    expected_password_files = {
        "db": ("MARIADB_ROOT_PASSWORD_FILE", "/run/elms-secrets/db-password"),
        "keycloak-db": ("POSTGRES_PASSWORD_FILE", "/run/elms-secrets/keycloak-db-password"),
    }
    for service_name, (key, expected_path) in expected_password_files.items():
        service = services.get(service_name, {})
        environment = service.get("environment", {}) if isinstance(service, dict) else {}
        actual_path = environment.get(key) if isinstance(environment, dict) else None
        if actual_path != expected_path:
            errors.append(f"{service_name}: {key} must point to {expected_path}")

    for service_name in ("db", "keycloak-db", "create-site", "backend", "keycloak"):
        service = services.get(service_name, {})
        depends_on = service.get("depends_on", {}) if isinstance(service, dict) else {}
        vault_dependency = depends_on.get("vault-agent") if isinstance(depends_on, dict) else None
        if not isinstance(vault_dependency, dict) or vault_dependency.get("condition") != "service_healthy":
            errors.append(f"{service_name}: Vault Agent health must gate startup")

    for service_name, service in services.items():
        if not isinstance(service, dict):
            continue
        for key, value in _environment_items(service.get("environment", {})):
            key = str(key)
            if key in FORBIDDEN_DIRECT_KEYS:
                errors.append(f"{service_name}: secret {key} is passed directly through Compose")
            if key.endswith("_PASSWORD") and key not in {"ELMS_SSO_REQUIRE"}:
                errors.append(f"{service_name}: password-like environment key {key} is not allowed")

    if re.search(r"(?<!\$)\$\{(?:DB_PASSWORD|ADMIN_PASSWORD|KEYCLOAK_DB_PASSWORD|KEYCLOAK_CLIENT_SECRET|YANDEX_CLIENT_SECRET)\b", agent_text):
        errors.append("production Compose must not interpolate runtime secret values")

    for template_name, expected_keys in TEMPLATE_KEYS.items():
        template = vault_dir / template_name
        if not template.is_file():
            errors.append(f"missing Vault runtime template: {template}")
            continue
        template_text = template.read_text(encoding="utf-8")
        if 'secret "elms/data/runtime"' not in template_text:
            errors.append(f"{template_name} must read the ELMS KV v2 runtime path")
        rendered_keys = set(re.findall(r"\.Data\.data\.([A-Z][A-Z0-9_]*)", template_text))
        missing = sorted(expected_keys - rendered_keys)
        if missing:
            errors.append(f"{template_name} misses keys: {', '.join(missing)}")
        if re.search(r"(?m)^\s*[A-Z][A-Z0-9_]*\s*=\s*[^{{\s]", template_text):
            errors.append(f"{template_name} contains a literal value")

    for name in ("db-password.tpl", "keycloak-db-password.tpl"):
        path = vault_dir / name
        if not path.is_file():
            errors.append(f"missing Vault file template: {path}")
        elif 'secret "elms/data/runtime"' not in path.read_text(encoding="utf-8"):
            errors.append(f"{name} must read the ELMS KV v2 runtime path")

    policy = vault_dir / "policies" / "elms-agent.hcl"
    if not policy.is_file():
        errors.append(f"missing least-privilege Vault policy: {policy}")
    else:
        policy_text = policy.read_text(encoding="utf-8")
        if 'path "elms/data/runtime"' not in policy_text or 'capabilities = ["read"]' not in policy_text:
            errors.append("elms-agent policy must allow read-only access to elms/data/runtime")
        if "secret/*" in policy_text or "create" in policy_text or "update" in policy_text:
            errors.append("elms-agent policy is broader than read-only runtime access")

    # A production env example is safe to commit only when secret-looking
    # values are absent.  Empty placeholders are intentionally accepted.
    example = compose_path.parent / ".env.prod.example"
    if example.is_file():
        for line_number, raw_line in enumerate(example.read_text(encoding="utf-8").splitlines(), 1):
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            if key in FORBIDDEN_DIRECT_KEYS and value.strip():
                errors.append(f".env.prod.example:{line_number} contains a secret value for {key}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compose", type=Path, default=Path("docker/compose.prod.yaml"))
    parser.add_argument("--vault-dir", type=Path, default=Path("docker/vault"))
    args = parser.parse_args()
    errors = validate(args.compose, args.vault_dir)
    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print("PASS: Vault-only production secret contract")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
