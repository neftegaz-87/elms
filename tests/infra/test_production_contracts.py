from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts" / "infra"


def run_script(name: str, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPTS / name), *arguments],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_compose_policy_passes_for_canonical_file() -> None:
    result = run_script("check_compose_policy.py", "--file", "docker/compose.prod.yaml")
    assert result.returncode == 0, result.stderr


def test_compose_policy_rejects_host_port(tmp_path: Path) -> None:
    document = yaml.safe_load((ROOT / "docker/compose.prod.yaml").read_text())
    document["services"]["db"]["ports"] = ["3306:3306"]
    path = tmp_path / "compose.yaml"
    path.write_text(yaml.safe_dump(document))
    result = run_script("check_compose_policy.py", "--file", str(path))
    assert result.returncode != 0
    assert "host ports" in result.stderr


def test_compose_policy_requires_digest_pinned_base_images() -> None:
    document = yaml.safe_load((ROOT / "docker/compose.prod.yaml").read_text())
    services = document["services"]
    for service_name in ("db", "redis-cache", "redis-queue", "keycloak-db"):
        image = services[service_name]["image"]
        assert "@sha256:" in image, f"{service_name} must be digest pinned"


def test_compose_policy_requires_successful_create_site_before_backend() -> None:
    document = yaml.safe_load((ROOT / "docker/compose.prod.yaml").read_text())
    depends_on = document["services"]["backend"]["depends_on"]
    assert depends_on["configurator"]["condition"] == "service_completed_successfully"
    assert depends_on["create-site"]["condition"] == "service_completed_successfully"
    assert depends_on["vault-agent"]["condition"] == "service_healthy"


def test_vault_secret_contract_passes() -> None:
    result = run_script("check_secret_contract.py")
    assert result.returncode == 0, result.stderr


def test_release_manifest_fixture_passes() -> None:
    result = run_script(
        "check_release_manifest.py",
        "--fixture",
        "tests/infra/fixtures/release-manifest.json",
    )
    assert result.returncode == 0, result.stderr


def test_release_manifest_rejects_latest_and_secrets(tmp_path: Path) -> None:
    value = json.loads((ROOT / "tests/infra/fixtures/release-manifest.json").read_text())
    value["images"][0]["ref"] = "ghcr.io/example/elms:latest"
    value["password"] = "must-not-be-here"
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(value))
    result = run_script("check_release_manifest.py", "--manifest", str(path))
    assert result.returncode != 0
    assert "latest" in result.stderr
    assert "secret-like" in result.stderr


def test_backup_manifest_and_disposable_restore(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    result = run_script("backup_runner.py", "manifest", "--output", str(manifest))
    assert result.returncode == 0, result.stderr
    assert "ELMS_REVIEW_HANDOFF_SECRET" not in manifest.read_text()

    target = tmp_path / "restore"
    result = run_script("backup_runner.py", "restore-preflight", "--target", str(target))
    assert result.returncode == 0, result.stderr
    assert (target / ".elms-disposable-restore").is_file()


def test_vault_preflight_dry_run_uses_non_secret_example(tmp_path: Path) -> None:
    env = tmp_path / ".env.prod"
    env.write_text(
        "\n".join(
            [
                "COMPOSE_PROJECT_NAME=elms-prod",
                "CUSTOM_IMAGE=ghcr.io/example/elms",
                "CUSTOM_TAG=prod-0123456",
                "KEYCLOAK_IMAGE=ghcr.io/example/elms-keycloak",
                "KEYCLOAK_TAG=prod-0123456",
                "VAULT_ROLE_ID_FILE=/run/elms/role-id",
                "VAULT_SECRET_ID_FILE=/run/elms/secret-id",
                "SITE_NAME=elms.example.com",
                "AUTH_HOSTNAME=auth.example.com",
                "SITE_HOST_NAME=https://elms.example.com",
                "KEYCLOAK_PUBLIC_URL=https://auth.example.com",
                "ELMS_REVIEW_URL=https://review.example.com/auth/login",
            ]
        )
        + "\n"
    )
    result = subprocess.run(
        ["bash", str(SCRIPTS / "vault_preflight.sh"), "--env-file", str(env), "--dry-run"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_vault_secret_contract_rejects_http_review_and_disabled_sso(tmp_path: Path) -> None:
    base = {
        "COMPOSE_PROJECT_NAME": "elms-prod",
        "CUSTOM_IMAGE": "ghcr.io/example/elms",
        "CUSTOM_TAG": "prod-0123456",
        "KEYCLOAK_IMAGE": "ghcr.io/example/elms-keycloak",
        "KEYCLOAK_TAG": "prod-0123456",
        "VAULT_ROLE_ID_FILE": "/run/elms/role-id",
        "VAULT_SECRET_ID_FILE": "/run/elms/secret-id",
        "SITE_NAME": "elms.example.com",
        "AUTH_HOSTNAME": "auth.example.com",
        "SITE_HOST_NAME": "https://elms.example.com",
        "KEYCLOAK_PUBLIC_URL": "https://auth.example.com",
        "ELMS_REVIEW_URL": "https://review.example.com/auth/login",
        "ELMS_SSO_REQUIRE": "1",
    }
    for suffix, override, expected in (
        ("http", {"ELMS_REVIEW_URL": "http://review.example.com/auth/login"}, "HTTPS"),
        ("sso", {"ELMS_SSO_REQUIRE": "0"}, "mandatory SSO"),
    ):
        values = {**base, **override}
        env = tmp_path / f".env.prod.{suffix}"
        env.write_text("\n".join(f"{key}={value}" for key, value in values.items()) + "\n")
        result = subprocess.run(
            ["bash", str(SCRIPTS / "vault_preflight.sh"), "--env-file", str(env), "--dry-run"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        assert result.returncode != 0
        assert expected in result.stderr


def test_vault_secret_contract_keeps_dev_synthetic_env_independent() -> None:
    dev = (ROOT / "docker/.env.dev.example").read_text()
    prod = (ROOT / "docker/.env.prod.example").read_text()
    assert "ELMS_REVIEW_URL=http://127.0.0.1:8765" in dev
    assert "ELMS_REVIEW_ALLOW_HTTP=1" in dev
    assert "ELMS_SSO_REQUIRE=0" in dev
    assert "ELMS_REVIEW_URL=https://" in prod
    assert "ELMS_REVIEW_ALLOW_HTTP=0" in prod
    assert "ELMS_SSO_REQUIRE=1" in prod
    assert "ELMS_REVIEW_HANDOFF_SECRET=" not in prod


def test_review_contract_has_no_fake_secret_or_http_production_path() -> None:
    compose = (ROOT / "docker/compose.prod.yaml").read_text()
    assert "ELMS_REVIEW_URL: ${ELMS_REVIEW_URL:?ELMS_REVIEW_URL is required}" in compose
    assert "ELMS_REVIEW_ALLOW_HTTP: ${ELMS_REVIEW_ALLOW_HTTP:-0}" in compose
    assert "ELMS_REVIEW_HANDOFF_SECRET" not in compose


def test_edge_preflight_and_wrapper_help() -> None:
    result = run_script("edge_cutover.py", "--root", ".", "preflight", "--staged")
    assert result.returncode == 0, result.stderr

    result = run_script("deploy_wrapper.py", "--help")
    assert result.returncode == 0, result.stderr


def test_edge_switch_requires_approval_and_evidence() -> None:
    result = run_script(
        "edge_cutover.py",
        "--root",
        ".",
        "switch",
        "--predecessor-evidence",
        "tests/infra/fixtures/edge-evidence.json",
    )
    assert result.returncode != 0
    assert "--approved" in result.stderr
