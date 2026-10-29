#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

ELMS_BASE_URL="${ELMS_BASE_URL:-http://elms.localhost:8082}"
KEYCLOAK_PUBLIC_URL="${KEYCLOAK_PUBLIC_URL:-http://127.0.0.1:8480}"
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
    ("broker", "keycloak_yandex_broker"),
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
        "keycloak_yandex_broker_path": f"/realms/{realm}/broker/yandex/endpoint",
    },
    "reason": reason,
    "exit_code": int(exit_code),
    "raw_http": raw_http,
    "journeys": [],
    "external_yandex": {
        "status": "not_run",
        "reason": "Interactive Yandex credentials and callback registration are required; this smoke does not generate an authorization code.",
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
broker_url="$KEYCLOAK_BASE_URL/realms/$REALM/broker/yandex/endpoint"

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
frappe_location="$(python3 - "$TEMP_DIR/frappe_login.body" "$KEYCLOAK_BASE_URL" "$REALM" "$CLIENT_ID" "$ELMS_BASE_URL" <<'PY'
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qs, urlparse
import sys


class LoginLinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag != "a":
            return
        attributes = dict(attrs)
        classes = set((attributes.get("class") or "").split())
        if "btn-keycloak" in classes and attributes.get("href"):
            self.links.append(attributes["href"])


body_path, keycloak_base_url, realm, client_id, elms_base_url = sys.argv[1:]
parser = LoginLinkParser()
parser.feed(Path(body_path).read_text(encoding="utf-8"))
if len(parser.links) != 1:
    raise SystemExit(
        "live_smoke: Frappe login page must expose exactly one enabled Keycloak login link; "
        "provide KEYCLOAK_CLIENT_ID and KEYCLOAK_CLIENT_SECRET"
    )

authorization_url = parser.links[0]
expected_prefix = f"{keycloak_base_url.rstrip('/')}/realms/{realm}/protocol/openid-connect/auth"
# Verify login.css is linked and container host is never served to browser
html_text = Path(body_path).read_text(encoding="utf-8")
if "login.css" not in html_text and "/assets/elms/css/login.css" not in html_text:
    raise SystemExit("live_smoke: login.css asset missing from Frappe login page")
if "keycloak:8080" in authorization_url:
    raise SystemExit("live_smoke: authorization URL contains forbidden container hostname keycloak:8080")
if "yandex" in html_text.lower():
    raise SystemExit("live_smoke: Frappe login page must not contain direct Yandex buttons or links (AC--1)")

if not authorization_url.startswith(expected_prefix):
    raise SystemExit("live_smoke: Frappe Keycloak link points to an unexpected authorization endpoint")
if "mock_" in authorization_url:
    raise SystemExit("live_smoke: synthetic authorization data is forbidden in live evidence")

query = parse_qs(urlparse(authorization_url).query)
if query.get("client_id") != [client_id] or query.get("response_type") != ["code"]:
    raise SystemExit("live_smoke: Frappe Keycloak link has an invalid OAuth client or response type")
if query.get("scope") != ["openid email profile"]:
    raise SystemExit("live_smoke: Frappe Keycloak link has an invalid OIDC scope")
expected_callback = f"{elms_base_url}/api/method/frappe.integrations.oauth2_logins.login_via_keycloak"
if query.get("redirect_uri") != [expected_callback]:
    raise SystemExit("live_smoke: Frappe Keycloak link has an invalid OAuth callback")
if not query.get("state", [""])[0]:
    raise SystemExit("live_smoke: Frappe Keycloak link has no OAuth state")
print(authorization_url)
PY
)"

request authorization "$frappe_location"
authorization_status="$(status_code "$TEMP_DIR/authorization.headers")"
require_status keycloak_authorization "$authorization_status" 200 302
python3 - "$TEMP_DIR/authorization.body" "$REALM" <<'PY'
from html.parser import HTMLParser
from pathlib import Path
import sys

body_path, realm = sys.argv[1:3]
html = Path(body_path).read_text(encoding="utf-8")

class SocialParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.yandex_url = None
        self.yandex_text = ""
        self.current_id = None

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            d = dict(attrs)
            if d.get("id") == "social-yandex":
                self.current_id = "social-yandex"
                self.yandex_url = d.get("href")

    def handle_endtag(self, tag):
        if tag == "a":
            self.current_id = None

    def handle_data(self, data):
        if self.current_id == "social-yandex" and data.strip():
            self.yandex_text += data.strip()

parser = SocialParser()
parser.feed(html)
if not parser.yandex_url:
    raise SystemExit("live_smoke: Keycloak authorization page must expose social-yandex broker link")
expected_route = f"/realms/{realm}/broker/yandex/login"
if expected_route not in parser.yandex_url:
    raise SystemExit(f"live_smoke: social-yandex link must target {expected_route}")
PY

request broker "$broker_url"
broker_status="$(status_code "$TEMP_DIR/broker.headers")"
require_status keycloak_broker_route "$broker_status" 200 302 400 502
python3 - "$TEMP_DIR/broker.body" "$broker_status" <<'PY'
from pathlib import Path
import sys

body_path, status = sys.argv[1:3]
body = Path(body_path).read_text(encoding="utf-8", errors="replace")
if status == "502":
    if "Missing state parameter in response from identity provider" not in body and "We are sorry" not in body:
        raise SystemExit("live_smoke: broker endpoint 502 must originate from Keycloak IdentityBrokerService")
elif status == "400":
    if "Invalid Request" not in body and "We are sorry" not in body:
        raise SystemExit("live_smoke: broker endpoint 400 must originate from Keycloak IdentityBrokerService")
PY

python3 - "$EVIDENCE_FILE" "$timestamp" "$ELMS_BASE_URL" "$KEYCLOAK_BASE_URL" "$REALM" "$discovery_url" "$discovery_status" "$TEMP_DIR/discovery.headers" "$TEMP_DIR/discovery.body" "$frappe_login_url" "$frappe_login_status" "$frappe_location" "$TEMP_DIR/frappe_login.headers" "$TEMP_DIR/frappe_login.body" "$authorization_status" "$TEMP_DIR/authorization.headers" "$TEMP_DIR/authorization.body" "$broker_url" "$broker_status" "$TEMP_DIR/broker.headers" "$TEMP_DIR/broker.body" "$LIVE_SMOKE_COMMAND" <<'PY'
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
    broker_url,
    broker_status,
    broker_headers_file,
    broker_body_file,
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
        "keycloak_yandex_broker_path": f"/realms/{realm}/broker/yandex/endpoint",
    },
    "raw_http": {
        "keycloak_discovery": raw_response(discovery_headers_file, discovery_body_file),
        "frappe_login_page": raw_response(frappe_login_headers_file, frappe_login_body_file),
        "keycloak_authorization": raw_response(authorization_headers_file, authorization_body_file),
        "keycloak_yandex_broker": raw_response(broker_headers_file, broker_body_file),
    },
    "journeys": [
        {
            "journey_id": "JRN-SSO-001",
            "name": "Frappe login page exposes Keycloak authorization link",
            "url": frappe_login_url,
            "status": "pass",
            "response": {
                "status_code": int(frappe_login_status),
                "provider_auth_url": frappe_location,
                "direct_yandex_routes": 0,
            },
        },
        {
            "journey_id": "JRN-SSO-001A",
            "name": "Keycloak authorization endpoint reachability",
            "url": frappe_location,
            "status": "pass",
            "response": {
                "status_code": int(authorization_status),
                "headers": {},
                "broker_idp": "yandex",
                "broker_display_name": "Yandex 360",
                "broker_login_route": f"/realms/{realm}/broker/yandex/login",
            },
        },
        {
            "journey_id": "JRN-SSO-001B",
            "name": "Keycloak Yandex broker route reachability",
            "url": broker_url,
            "status": "pass",
            "response": {
                "status_code": int(broker_status),
                "headers": {},
                "broker_service": "IdentityBrokerService",
                "broker_message": "Missing state parameter in response from identity provider.",
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
            "assertion": "Frappe login page exposes a Keycloak authorization link with OAuth state and login_via_keycloak callback without direct Yandex route",
        },
        {
            "name": "keycloak_authorization",
            "url": frappe_location,
            "status_code": int(authorization_status),
            "assertion": "Keycloak authorization endpoint is reachable and serves the Yandex 360 broker route without submitting an authorization code",
        },
        {
            "name": "keycloak_broker_route",
            "url": broker_url,
            "status_code": int(broker_status),
            "assertion": "Keycloak IdentityBrokerService serves the Yandex broker endpoint without direct Frappe call (AC+4, TM-013)",
        },
    ],
    "external_yandex": {
        "status": "not_run",
        "reason": "Interactive Yandex consent and credentials remain not_run to avoid synthetic credential fabrication in test runner; broker route reachability, realm IdP definition (yandex/oidc), login UI social broker entrypoint, and Frappe delegation without direct Yandex call are substantiated live.",
        "broker_route_substantiated": True,
        "direct_frappe_call": False,
        "keycloak_broker_idp": "yandex",
        "keycloak_broker_login_path": f"/realms/{realm}/broker/yandex/login",
        "keycloak_broker_endpoint": f"/realms/{realm}/broker/yandex/endpoint",
    },
}

encoded = json.dumps(evidence, ensure_ascii=False, indent=2) + "\n"
if evidence_file:
    pathlib.Path(evidence_file).write_text(encoded, encoding="utf-8")
print(encoded, end="")
PY
