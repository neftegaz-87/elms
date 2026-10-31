from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts" / "infra"
FIXTURES = ROOT / "tests" / "infra" / "fixtures"


def run_bash(script: str, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(SCRIPTS / script), *arguments],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def production_env(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "COMPOSE_PROJECT_NAME=elms-prod",
                "CUSTOM_IMAGE=ghcr.io/example/elms",
                "CUSTOM_TAG=prod-0123456",
                "KEYCLOAK_IMAGE=ghcr.io/example/elms-keycloak",
                "KEYCLOAK_TAG=prod-0123456",
                "VAULT_IMAGE=hashicorp/vault:1.18.1@sha256:" + "a" * 64,
                "VAULT_ROLE_ID_FILE=/run/elms/role-id",
                "VAULT_SECRET_ID_FILE=/run/elms/secret-id",
                "SITE_NAME=elms.example.com",
                "AUTH_HOSTNAME=auth.example.com",
                "SITE_HOST_NAME=https://elms.example.com",
                "KEYCLOAK_PUBLIC_URL=https://auth.example.com",
                "ELMS_REVIEW_URL=https://review.example.com/auth/login",
                "ELMS_SSO_REQUIRE=1",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


@pytest.mark.parametrize(
    "fixture_name",
    ["vault-sealed.json", "vault-unavailable.json", "vault-unauthorized.json", "vault-missing-path.json"],
)
def test_vault_preflight_rejects_negative_states_without_values(
    tmp_path: Path, fixture_name: str
) -> None:
    env_file = tmp_path / ".env.prod"
    production_env(env_file)
    fixture = FIXTURES / fixture_name

    result = run_bash(
        "vault_preflight.sh",
        "--env-file",
        str(env_file),
        "--dry-run",
        "--fixture",
        str(fixture),
    )

    assert result.returncode != 0
    assert "synthetic-fixture-value" not in result.stdout + result.stderr
    assert "synthetic-db-value" not in result.stdout + result.stderr


def test_vault_preflight_redacts_positive_fixture(tmp_path: Path) -> None:
    env_file = tmp_path / ".env.prod"
    production_env(env_file)

    result = run_bash(
        "vault_preflight.sh",
        "--env-file",
        str(env_file),
        "--dry-run",
        "--fixture",
        str(FIXTURES / "vault-redaction.json"),
    )

    assert result.returncode == 0, result.stderr
    assert "synthetic-fixture-value-must-not-be-logged" not in result.stdout + result.stderr
    assert "redacted" in result.stdout


@pytest.mark.parametrize("action", ["bootstrap", "rotate", "revoke"])
def test_bootstrap_fixture_actions_are_status_only(action: str) -> None:
    result = run_bash(
        "vault_bootstrap.sh",
        action,
        "--fixture",
        str(FIXTURES / "vault-synthetic-snapshot.json"),
    )

    assert result.returncode == 0, result.stderr
    output = result.stdout + result.stderr
    assert "synthetic-db-value-must-not-be-logged" not in output
    assert "synthetic-client-value-must-not-be-logged" not in output
    assert "redacted" in output


def test_snapshot_fixture_restore_is_disposable_and_redacted(tmp_path: Path) -> None:
    snapshot = tmp_path / "raft.snap"
    target = tmp_path / "restore-target"
    fixture = FIXTURES / "vault-synthetic-snapshot.json"

    saved = run_bash(
        "vault_snapshot.sh",
        "snapshot",
        "--fixture",
        str(fixture),
        "--output",
        str(snapshot),
    )
    assert saved.returncode == 0, saved.stderr

    restored = run_bash(
        "vault_snapshot.sh",
        "restore",
        "--fixture",
        "--input",
        str(snapshot),
        "--target",
        str(target),
    )
    assert restored.returncode == 0, restored.stderr
    output = restored.stdout + restored.stderr
    assert "synthetic-db-value-must-not-be-logged" not in output
    assert "redacted" in output

    marker = target / ".elms-disposable-restore"
    assert marker.is_file()
    marker_data = json.loads(marker.read_text(encoding="utf-8"))
    assert marker_data["schema"] == "elms-vault-disposable-restore/v1"
    assert marker_data["status"] == "restored"
    assert marker_data["secret_keys"] == ["DB_PASSWORD", "KEYCLOAK_CLIENT_SECRET"]
    assert "synthetic-db-value" not in marker.read_text(encoding="utf-8")


def test_production_surfaces_use_single_secret_source() -> None:
    bounded = [
        ROOT / "scripts/infra/vault_bootstrap.sh",
        ROOT / "scripts/infra/vault_snapshot.sh",
        ROOT / "scripts/infra/vault_preflight.sh",
        ROOT / "scripts/infra/check_secret_contract.py",
        ROOT / "docker/vault/keycloak.env.tpl",
        ROOT / "docker/keycloak/entrypoint.sh",
        ROOT / "docker/keycloak/realm-elms.json",
        ROOT / "docs/operations/elms-production.md",
    ]
    text = "\n".join(path.read_text(encoding="utf-8") for path in bounded)
    assert "KEYCLOAK_" + "FALL" + "BACK_PASSWORD" not in text
    assert "VAULT_" + "TOKEN" not in text


def test_realm_does_not_import_removed_local_user() -> None:
    realm = (ROOT / "docker/keycloak/realm-elms.json").read_text(encoding="utf-8")
    assert "fall" + "back.user" not in realm


def test_production_compose_does_not_expand_rendered_passwords_in_compose() -> None:
    compose = (ROOT / "docker/compose.prod.yaml").read_text(encoding="utf-8")
    assert '--admin-password="$${ADMIN_PASSWORD}"' not in compose
    assert '--db-root-password="$${DB_PASSWORD}"' not in compose
