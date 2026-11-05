from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts" / "infra"


def run_script(
    name: str,
    *arguments: str,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    process_env = os.environ.copy()
    if env:
        process_env.update(env)
    return subprocess.run(
        [sys.executable, str(SCRIPTS / name), *arguments],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        env=process_env,
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


def fake_docker(tmp_path: Path, *, fail_on_up: bool = False) -> tuple[Path, Path]:
    executable = tmp_path / "docker"
    calls = tmp_path / "docker.calls"
    code = [
        "#!/usr/bin/env python3",
        "import os, sys",
        "with open(os.environ['DOCKER_CALL_LOG'], 'a', encoding='utf-8') as f:",
        "    f.write(' '.join(sys.argv[1:]) + chr(10))",
        "if os.environ.get('FAKE_DOCKER_FAIL_UP') and 'up' in sys.argv:",
        "    sys.exit(42)",
    ]
    executable.write_text(chr(10).join(code) + chr(10), encoding="utf-8")
    executable.chmod(0o755)
    return executable, calls


def fake_systemctl(tmp_path: Path) -> tuple[Path, Path]:
    executable = tmp_path / "systemctl"
    calls = tmp_path / "systemctl.calls"
    code = [
        "#!/usr/bin/env python3",
        "import os, sys",
        "with open(os.environ['SYSTEMCTL_CALL_LOG'], 'a', encoding='utf-8') as f:",
        "    f.write(' '.join(sys.argv[1:]) + chr(10))",
    ]
    executable.write_text(chr(10).join(code) + chr(10), encoding="utf-8")
    executable.chmod(0o755)
    return executable, calls


def fake_curl(tmp_path: Path) -> tuple[Path, Path]:
    executable = tmp_path / "curl"
    calls = tmp_path / "curl.calls"
    code = [
        "#!/usr/bin/env python3",
        "import os, sys",
        "with open(os.environ['CURL_CALL_LOG'], 'a', encoding='utf-8') as f:",
        "    f.write(' '.join(sys.argv[1:]) + chr(10))",
    ]
    executable.write_text(chr(10).join(code) + chr(10), encoding="utf-8")
    executable.chmod(0o755)
    return executable, calls


def test_edge_switch_requires_approval_and_evidence() -> None:
    for action in ("switch", "rollback"):
        result = run_script(
            "edge_cutover.py",
            "--root",
            ".",
            action,
            "--predecessor-evidence",
            "tests/infra/fixtures/edge-evidence.json",
        )
        assert result.returncode != 0
        assert "--approved" in result.stderr

        result_no_exec = run_script(
            "edge_cutover.py",
            "--root",
            ".",
            action,
            "--approved",
            "--predecessor-evidence",
            "tests/infra/fixtures/edge-evidence.json",
        )
        assert result_no_exec.returncode != 0
        assert "--execute" in result_no_exec.stderr

        result_no_ev = run_script(
            "edge_cutover.py",
            "--root",
            ".",
            action,
            "--approved",
            "--execute",
        )
        assert result_no_ev.returncode != 0
        assert "predecessor edge evidence file is required" in result_no_ev.stderr


def test_edge_rollback_requires_approved_and_execute() -> None:
    result = run_script(
        "edge_cutover.py",
        "--root",
        ".",
        "rollback",
        "--predecessor-evidence",
        "tests/infra/fixtures/edge-evidence.json",
    )
    assert result.returncode != 0
    assert "--approved" in result.stderr

    result_no_exec = run_script(
        "edge_cutover.py",
        "--root",
        ".",
        "rollback",
        "--approved",
        "--predecessor-evidence",
        "tests/infra/fixtures/edge-evidence.json",
    )
    assert result_no_exec.returncode != 0
    assert "--execute" in result_no_exec.stderr

    result_no_ev = run_script(
        "edge_cutover.py",
        "--root",
        ".",
        "rollback",
        "--approved",
        "--execute",
    )
    assert result_no_ev.returncode != 0
    assert "predecessor edge evidence file is required" in result_no_ev.stderr


def test_edge_status_json_inspection() -> None:
    result = run_script("edge_cutover.py", "--root", ".", "status")
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert "http_80_in_use" in payload
    assert "https_443_in_use" in payload
    assert "staged_18080_in_use" in payload
    assert "port ownership is evidence only" in payload.get("note", "")


def test_edge_evidence_stale_or_missing(tmp_path: Path) -> None:
    missing_path = tmp_path / "does-not-exist.json"
    result_missing = run_script(
        "edge_cutover.py",
        "--root",
        ".",
        "switch",
        "--approved",
        "--execute",
        "--predecessor-evidence",
        str(missing_path),
    )
    assert result_missing.returncode != 0
    assert "missing" in result_missing.stderr

    stale_file = tmp_path / "stale-evidence.json"
    valid_fixture = ROOT / "tests/infra/fixtures/edge-evidence.json"
    stale_file.write_text(valid_fixture.read_text(encoding="utf-8"), encoding="utf-8")
    stale_mtime = time.time() - (48 * 3600)
    os.utime(stale_file, (stale_mtime, stale_mtime))

    result_stale = run_script(
        "edge_cutover.py",
        "--root",
        ".",
        "switch",
        "--approved",
        "--execute",
        "--predecessor-evidence",
        str(stale_file),
        "--max-age-hours",
        "24",
    )
    assert result_stale.returncode != 0
    assert "stale" in result_stale.stderr

    unapproved_file = tmp_path / "unapproved-evidence.json"
    unapproved_data = json.loads(valid_fixture.read_text(encoding="utf-8"))
    unapproved_data["owner_approved"] = False
    unapproved_file.write_text(json.dumps(unapproved_data), encoding="utf-8")

    result_unapproved = run_script(
        "edge_cutover.py",
        "--root",
        ".",
        "switch",
        "--approved",
        "--execute",
        "--predecessor-evidence",
        str(unapproved_file),
    )
    assert result_unapproved.returncode != 0
    assert "owner approval" in result_unapproved.stderr

    bad_gate_file = tmp_path / "bad-gate-evidence.json"
    bad_gate_data = json.loads(valid_fixture.read_text(encoding="utf-8"))
    bad_gate_data["backup"]["status"] = "stale"
    bad_gate_file.write_text(json.dumps(bad_gate_data), encoding="utf-8")

    result_bad_gate = run_script(
        "edge_cutover.py",
        "--root",
        ".",
        "switch",
        "--approved",
        "--execute",
        "--predecessor-evidence",
        str(bad_gate_file),
    )
    assert result_bad_gate.returncode != 0
    assert "missing a passing backup gate" in result_bad_gate.stderr


def test_edge_switch_refuses_occupied_ports(monkeypatch, tmp_path: Path) -> None:
    content = (SCRIPTS / "edge_cutover.py").read_text(encoding="utf-8")
    assert "port_state(80) or port_state(443)" in content
    assert "80/443 are still occupied; host edge must be released explicitly" in content
    assert "cutover_lock" in content
    assert "ELMS_EDGE_LOCK" in content


def test_caddy_staged_and_edge_routing_contract() -> None:
    caddy = (ROOT / "docker/caddy/Caddyfile").read_text(encoding="utf-8")
    staged_caddy = (ROOT / "docker/caddy/Caddyfile.staged").read_text(encoding="utf-8")
    compose_prod = (ROOT / "docker/compose.prod.yaml").read_text(encoding="utf-8")
    compose_staged = (ROOT / "docker/compose.prod.staged.yaml").read_text(encoding="utf-8")
    compose_edge = (ROOT / "docker/compose.prod.edge.yaml").read_text(encoding="utf-8")

    assert "reverse_proxy frontend" in caddy
    assert "reverse_proxy keycloak" in caddy
    assert "reverse_proxy frontend" in staged_caddy
    assert "reverse_proxy keycloak" in staged_caddy

    assert "/healthz" in caddy
    assert "/healthz" in staged_caddy

    for content in (caddy, staged_caddy):
        assert re.search(r"review|first-party", content, re.IGNORECASE)
        assert not re.search(r"catch-all|catchall", content, re.IGNORECASE)
        assert not re.search(r"unknown.*200|200.*unknown", content, re.IGNORECASE)

    assert "ports:" not in compose_prod
    assert "127.0.0.1:" in compose_staged
    assert "18080" in compose_staged
    assert "${HTTP_PUBLISH_PORT:-80}:80" in compose_edge
    assert "${HTTPS_PUBLISH_PORT:-443}:443" in compose_edge

    assert "caddy-data:/data" in compose_prod
    assert "caddy-config:/config" in compose_prod
    assert not re.search(r"(\.key|private_key|privkey\.pem)", compose_prod, re.IGNORECASE)
    assert not re.search(r"(\.key|private_key|privkey\.pem)", compose_edge, re.IGNORECASE)

    # RC-003: public HTTP blocks match /healthz and explicitly fallback to 404 for unmatched paths
    assert caddy.count('respond "Not Found" 404') >= 2
    assert staged_caddy.count('respond "Not Found" 404') >= 1

    site_http_match = re.search(
        r"http://\{\$SITE_NAME\}\s*\{(?P<body>.*?)\n\}",
        caddy,
        re.DOTALL,
    )
    assert site_http_match is not None, "Missing http://{$SITE_NAME} block in Caddyfile"
    assert "@health path /healthz" in site_http_match.group("body")
    assert 'respond "Not Found" 404' in site_http_match.group("body")

    auth_http_match = re.search(
        r"http://\{\$AUTH_HOSTNAME\}\s*\{(?P<body>.*?)\n\}",
        caddy,
        re.DOTALL,
    )
    assert auth_http_match is not None, "Missing http://{$AUTH_HOSTNAME} block in Caddyfile"
    assert "@health path /healthz" in auth_http_match.group("body")
    assert 'respond "Not Found" 404' in auth_http_match.group("body")


def test_edge_rollback_drill_contract(tmp_path: Path) -> None:
    docker, docker_calls = fake_docker(tmp_path)
    systemctl, systemctl_calls = fake_systemctl(tmp_path)
    curl, curl_calls = fake_curl(tmp_path)

    evidence_file = tmp_path / "edge-evidence.json"
    evidence_file.write_text(
        (ROOT / "tests/infra/fixtures/edge-evidence.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    lock_file = tmp_path / "edge.lock"
    environment = {
        "PATH": f"{tmp_path}:{os.environ['PATH']}",
        "DOCKER_CALL_LOG": str(docker_calls),
        "SYSTEMCTL_CALL_LOG": str(systemctl_calls),
        "CURL_CALL_LOG": str(curl_calls),
        "ELMS_EDGE_LOCK": str(lock_file),
    }

    env_fail = {**environment, "FAKE_DOCKER_FAIL_UP": "1"}
    result_fail = run_script(
        "edge_cutover.py",
        "--root",
        ".",
        "switch",
        "--approved",
        "--execute",
        "--predecessor-evidence",
        str(evidence_file),
        env=env_fail,
    )
    assert result_fail.returncode != 0

    result_rollback = run_script(
        "edge_cutover.py",
        "--root",
        ".",
        "rollback",
        "--approved",
        "--execute",
        "--predecessor-evidence",
        str(evidence_file),
        env=environment,
    )
    assert result_rollback.returncode == 0, f"Rollback drill failed: {result_rollback.stderr}\n{result_rollback.stdout}"
    json_lines = [line for line in result_rollback.stdout.strip().splitlines() if line.startswith('{')]
    assert json_lines, 'No JSON output in stdout'
    data = json.loads(json_lines[-1])
    assert data == {"action": "rollback", "executed": True}

    docker_log = docker_calls.read_text(encoding="utf-8")
    assert "stop caddy" in docker_log
    systemctl_log = systemctl_calls.read_text(encoding="utf-8")
    assert "start caddy" in systemctl_log
    assert "is-active --quiet caddy" in systemctl_log
    curl_log = curl_calls.read_text(encoding="utf-8")
    assert "http://127.0.0.1/healthz" in curl_log


def test_edge_cutover_runbook_documentation() -> None:
    content = (ROOT / "docs/operations/elms-production.md").read_text(encoding="utf-8")
    assert "## Edge cutover" in content
    assert "maintenance window" in content.lower()
    assert "rollback budget" in content.lower()
    assert "scripts/infra/edge_cutover.py" in content
    assert "switch" in content
    assert "rollback" in content
    assert "systemctl start caddy" in content
    assert "systemctl is-active" in content
    assert "--approved" in content
    assert "--execute" in content
    assert "--predecessor-evidence" in content
