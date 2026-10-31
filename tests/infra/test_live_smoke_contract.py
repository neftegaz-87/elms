from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[2]


def test_live_smoke_defaults_to_dev_public_keycloak_url() -> None:
    script = (ROOT / "scripts/live_smoke.sh").read_text()
    match = re.search(r'^KEYCLOAK_PUBLIC_URL="\$\{KEYCLOAK_PUBLIC_URL:-([^}]+)\}"$', script, re.MULTILINE)

    assert match is not None
    assert match.group(1) == "http://elms-keycloak.localhost:8480"
