#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

ELMS_BASE_URL="${ELMS_BASE_URL:-http://elms.localhost:8082}"
KEYCLOAK_PUBLIC_URL="${KEYCLOAK_PUBLIC_URL:-http://elms-keycloak.localhost:8480}"
KEYCLOAK_BASE_URL="${KEYCLOAK_BASE_URL:-$KEYCLOAK_PUBLIC_URL}"
REALM="${KEYCLOAK_REALM:-elms}"
CLIENT_ID="${KEYCLOAK_CLIENT_ID:-elms-frappe}"
CURL_TIMEOUT="${CURL_TIMEOUT:-15}"
EVIDENCE_FILE="${EVIDENCE_FILE:-}"
LIVE_SMOKE_COMMAND="${LIVE_SMOKE_COMMAND:-bash scripts/live_smoke.sh}"

for dependency in curl python3; do
    if ! command -v "$dependency" >/dev/null 2>&1; then
        echo "live_smoke: missing dependency: $dependency" >&2
        exit 127
    fi
done

TEMP_DIR="$(mktemp -d)"
failure_reason=""

write_failure_evidence() {
    local exit_code="$1"
    [[ -n "$EVIDENCE_FILE" ]] || return 0
    python3 - "$EVIDENCE_FILE" "$timestamp" "$ELMS_BASE_URL" "$KEYCLOAK_BASE_URL" "$REALM" "$LIVE_SMOKE_COMMAND" "$exit_code" "${failure_reason:-live smoke exited before all checks completed}" "$TEMP_DIR" <<'PY' || true
import json
import pathlib
import sys

evidence_file, timestamp, elms_base_url, keycloak_base_url, realm, command, exit_code, reason, temp_dir = sys.argv[1:]

raw_http = {}
for name, evidence_name in (
    ("discovery", "keycloak_discovery"),
    ("frappe_login", "frappe_login_page"),
    ("authorization", "keycloak_authorization"),
):
    headers_path = pathlib.Path(temp_dir) / f"{name}.headers"
    body_path = pathlib.Path(temp_dir) / f"{name}.body"
    if headers_path.exists() or body_path.exists():
        raw_http[evidence_name] = {
            "headers": headers_path.read_text(encoding="utf-8") if headers_path.exists() else "",
            "body": body_path.read_text(encoding="utf-8") if body_path.exists() else "",
        }
evidence = {
    "schema": "sso-browser-api-trace/v1",
    "status": "blocked",
    "live_evidence": False,
    "evidence_type": "runtime_http_error",
    "timestamp": timestamp,
    "command": command,
    "base_urls": {
        "frappe": elms_base_url,
        "keycloak": keycloak_base_url,
    },
    "contract": {
        "frappe_oauth_callback": f"{elms_base_url}/api/method/frappe.integrations.oauth2_logins.login_via_keycloak",
        "frappe_login_path": "/login",
        "keycloak_authorization_path": f"/realms/{realm}/protocol/openid-connect/auth",
    },
    "reason": reason,
    "exit_code": int(exit_code),
    "raw_http": raw_http,
    "journeys": [],
    "legacy_broker": {
        "status": "removed",
        "reason": "The ELMS realm is Keycloak-only; no external identity-provider credentials or route are required.",
    },
}
pathlib.Path(evidence_file).write_text(
    json.dumps(evidence, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)
PY
}

cleanup() {
    local exit_code="$?"
    if (( exit_code != 0 )); then
        write_failure_evidence "$exit_code"
    fi
    rm -rf "$TEMP_DIR"
    exit "$exit_code"
}

trap cleanup EXIT

request() {
    local name="$1"
    local url="$2"
    local -a curl_args=(
        --silent
        --show-error
        --max-time "$CURL_TIMEOUT"
        --dump-header "$TEMP_DIR/$name.headers"
        --output "$TEMP_DIR/$name.body"
    )
    if [[ "$url" == http://elms.localhost:* ]]; then
        curl_args+=(--resolve elms.localhost:8082:127.0.0.1)
    fi
    if ! curl "${curl_args[@]}" "$url"; then
        failure_reason="request failed: $url"
        echo "live_smoke: request failed: $url" >&2
        exit 1
    fi
}

status_code() {
    awk '$1 ~ /^HTTP\/[0-9.]+$/ { code=$2 } END { print code }' "$1"
}

location_header() {
    awk 'tolower($1) == "location:" { sub(/^[^:]+:[[:space:]]*/, ""); sub(/\r$/, ""); print; exit }' "$1"
}

require_status() {
    local name="$1"
    local actual="$2"
    shift 2
    local expected
    for expected in "$@"; do
        if [[ "$actual" == "$expected" ]]; then
            return 0
        fi
    done
    failure_reason="$name returned unexpected HTTP status: ${actual:-missing}"
    echo "live_smoke: $name returned unexpected HTTP status: ${actual:-missing}" >&2
    exit 1
}

timestamp="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
discovery_url="$KEYCLOAK_BASE_URL/realms/$REALM/.well-known/openid-configuration"
frappe_login_url="$ELMS_BASE_URL/login"

request discovery "$discovery_url"
discovery_status="$(status_code "$TEMP_DIR/discovery.headers")"
require_status keycloak_discovery "$discovery_status" 200
python3 - "$TEMP_DIR/discovery.body" "$discovery_url" "$REALM" <<'PY'
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
realm = sys.argv[3]
required = {
    "issuer",
    "authorization_endpoint",
    "token_endpoint",
    "userinfo_endpoint",
}
missing = sorted(required.difference(payload))
if missing:
    raise SystemExit(f"live_smoke: Keycloak discovery is missing: {', '.join(missing)}")
if not payload["issuer"].rstrip("/").endswith(f"/realms/{realm}"):
    raise SystemExit(f"live_smoke: unexpected Keycloak issuer in {sys.argv[2]}")
PY

request frappe_login "$frappe_login_url"
frappe_login_status="$(status_code "$TEMP_DIR/frappe_login.headers")"
require_status frappe_login_page "$frappe_login_status" 200
python3 - "$TEMP_DIR/frappe_login.body" <<'PY'
from html.parser import HTMLParser
from pathlib import Path
import sys


class LoginSurfaceParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.keycloak_links = []
        self.has_form_login = False
        self.has_login_js = False

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        classes = set((attributes.get("class") or "").split())
        if tag == "form" and "form-login" in classes:
            self.has_form_login = True
        if tag == "a":
            if "btn-keycloak" in classes and attributes.get("href"):
                self.keycloak_links.append(attributes["href"])
        if tag == "script":
            src = attributes.get("src") or ""
            if "login-keycloak.js" in src:
                self.has_login_js = True


html_text = Path(sys.argv[1]).read_text(encoding="utf-8")
parser = LoginSurfaceParser()
parser.feed(html_text)
if not parser.has_form_login:
    raise SystemExit("live_smoke: Frappe login page must expose the standard password form")
if not parser.has_login_js and "login-keycloak.js" not in html_text:
    raise SystemExit("live_smoke: login-keycloak.js asset missing from Frappe login page")
if parser.keycloak_links:
    raise SystemExit(
        "live_smoke: Frappe login page must not expose a separate Keycloak OAuth button; "
        "password form is the sole Keycloak path"
    )
if "login.css" not in html_text and "/assets/elms/css/login.css" not in html_text:
    raise SystemExit("live_smoke: login.css asset missing from Frappe login page")
if "yandex" in html_text.lower():
    raise SystemExit("live_smoke: Frappe login page must not contain direct Yandex buttons or links (AC--1)")
PY

request sso_auth_url "$ELMS_BASE_URL/api/method/elms.sso.login.get_sso_authorization_url"
sso_auth_status="$(status_code "$TEMP_DIR/sso_auth_url.headers")"
require_status sso_authorization_url "$sso_auth_status" 200
frappe_location="$(python3 - "$TEMP_DIR/sso_auth_url.body" "$KEYCLOAK_BASE_URL" "$REALM" "$CLIENT_ID" "$ELMS_BASE_URL" <<'PY'
from pathlib import Path
from urllib.parse import parse_qs, urlparse
import json
import sys

body_path, keycloak_base_url, realm, client_id, elms_base_url = sys.argv[1:]
payload = json.loads(Path(body_path).read_text(encoding="utf-8"))
message = payload.get("message") or {}
authorization_url = str(message.get("auth_url") or "").strip()
if not authorization_url:
    raise SystemExit("live_smoke: get_sso_authorization_url did not return auth_url")

expected_prefix = f"{keycloak_base_url.rstrip('/')}/realms/{realm}/protocol/openid-connect/auth"
if "keycloak:8080" in authorization_url:
    raise SystemExit("live_smoke: authorization URL contains forbidden container hostname keycloak:8080")
if not authorization_url.startswith(expected_prefix):
    raise SystemExit("live_smoke: SSO authorization URL points to an unexpected endpoint")
if "mock_" in authorization_url:
    raise SystemExit("live_smoke: synthetic authorization data is forbidden in live evidence")

query = parse_qs(urlparse(authorization_url).query)
if query.get("client_id") != [client_id] or query.get("response_type") != ["code"]:
    raise SystemExit("live_smoke: SSO authorization URL has an invalid OAuth client or response type")
scope = query.get("scope", [""])[0].split()
if sorted(scope) != ["email", "openid", "profile"]:
    raise SystemExit("live_smoke: SSO authorization URL has an invalid OIDC scope")
expected_callback = f"{elms_base_url}/api/method/frappe.integrations.oauth2_logins.login_via_keycloak"
if query.get("redirect_uri") != [expected_callback]:
    raise SystemExit("live_smoke: SSO authorization URL has an invalid OAuth callback")
if not query.get("state", [""])[0]:
    raise SystemExit("live_smoke: SSO authorization URL has no OAuth state")
print(authorization_url)
PY
)"

request authorization "$frappe_location"
authorization_status="$(status_code "$TEMP_DIR/authorization.headers")"
require_status keycloak_authorization "$authorization_status" 200 302
python3 - "$TEMP_DIR/authorization.body" <<'PY'
from pathlib import Path
import sys

body_path = sys.argv[1]
html = Path(body_path).read_text(encoding="utf-8")
if "yandex" in html.lower() or "kc_idp_hint" in html.lower():
    raise SystemExit("live_smoke: Keycloak authorization page exposes a removed external IdP path")
PY

python3 - "$EVIDENCE_FILE" "$timestamp" "$ELMS_BASE_URL" "$KEYCLOAK_BASE_URL" "$REALM" "$discovery_url" "$discovery_status" "$TEMP_DIR/discovery.headers" "$TEMP_DIR/discovery.body" "$frappe_login_url" "$frappe_login_status" "$frappe_location" "$TEMP_DIR/frappe_login.headers" "$TEMP_DIR/frappe_login.body" "$authorization_status" "$TEMP_DIR/authorization.headers" "$TEMP_DIR/authorization.body" "$LIVE_SMOKE_COMMAND" <<'PY'
import json
import pathlib
import sys

(
    evidence_file,
    timestamp,
    elms_base_url,
    keycloak_base_url,
    realm,
    discovery_url,
    discovery_status,
    discovery_headers_file,
    discovery_body_file,
    frappe_login_url,
    frappe_login_status,
    frappe_location,
    frappe_login_headers_file,
    frappe_login_body_file,
    authorization_status,
    authorization_headers_file,
    authorization_body_file,
    command,
) = sys.argv[1:]


def raw_response(headers_file: str, body_file: str) -> dict[str, str]:
    return {
        "headers": pathlib.Path(headers_file).read_text(encoding="utf-8"),
        "body": pathlib.Path(body_file).read_text(encoding="utf-8"),
    }

evidence = {
    "schema": "sso-browser-api-trace/v1",
    "status": "pass",
    "live_evidence": True,
    "evidence_type": "runtime_http",
    "timestamp": timestamp,
    "command": command,
    "exit_code": 0,
    "base_urls": {
        "frappe": elms_base_url,
        "keycloak": keycloak_base_url,
    },
    "contract": {
        "frappe_oauth_callback": f"{elms_base_url}/api/method/frappe.integrations.oauth2_logins.login_via_keycloak",
        "frappe_login_path": "/login",
        "keycloak_authorization_path": f"/realms/{realm}/protocol/openid-connect/auth",
    },
    "raw_http": {
        "keycloak_discovery": raw_response(discovery_headers_file, discovery_body_file),
        "frappe_login_page": raw_response(frappe_login_headers_file, frappe_login_body_file),
        "keycloak_authorization": raw_response(authorization_headers_file, authorization_body_file),
    },
    "journeys": [
        {
            "journey_id": "JRN-SSO-001",
            "name": "Frappe login page exposes Keycloak-bound password form only",
            "url": frappe_login_url,
            "status": "pass",
            "response": {
                "status_code": int(frappe_login_status),
                "provider_auth_url": frappe_location,
                "direct_yandex_routes": 0,
                "oauth_keycloak_button": 0,
            },
        },
        {
            "journey_id": "JRN-SSO-001A",
            "name": "Keycloak authorization endpoint reachability via SSO API",
            "url": frappe_location,
            "status": "pass",
            "response": {
                "status_code": int(authorization_status),
                "headers": {},
            },
        },
    ],
    "checks": [
        {
            "name": "keycloak_discovery",
            "url": discovery_url,
            "status_code": int(discovery_status),
            "assertion": "OIDC discovery contains issuer and authorization/token/userinfo endpoints",
        },
        {
            "name": "frappe_login_page",
            "url": frappe_login_url,
            "status_code": int(frappe_login_status),
            "provider_auth_url": frappe_location,
            "assertion": "Frappe login page exposes password form + login-keycloak.js without OAuth Keycloak button or direct Yandex route",
        },
        {
            "name": "keycloak_authorization",
            "url": frappe_location,
            "status_code": int(authorization_status),
            "assertion": "Keycloak authorization endpoint is reachable without an external IdP hint or broker route",
        },
    ],
    "legacy_broker": {
        "status": "removed",
        "reason": "Keycloak-only realm has no external identity-provider route or secret dependency.",
    },
}

encoded = json.dumps(evidence, ensure_ascii=False, indent=2) + "\n"
if evidence_file:
    pathlib.Path(evidence_file).write_text(encoded, encoding="utf-8")
print(encoded, end="")
PY
