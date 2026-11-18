#!/usr/bin/env python3
"""Run automated browser QA tests for ELMS Keycloak Login UI via Playwright."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
import json
import os
from pathlib import Path
import re
import shlex
import sys
from threading import Thread
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parent.parent
ARTIFACTS_DIR = ROOT / "browser-artifacts"
RUNTIME_ENV_KEYS = ("ELMS_BROWSER_TEST_USERNAME", "ELMS_BROWSER_TEST_PASSWORD")
ENV_REFERENCE = re.compile(r"\$(?:\{(?P<braced>[A-Za-z_][A-Za-z0-9_]*)\}|(?P<bare>[A-Za-z_][A-Za-z0-9_]*))")


def _expand_env_references(value: str, file_values: dict[str, str]) -> str:
    expanded = value
    for _ in range(len(file_values) + 1):
        next_value = ENV_REFERENCE.sub(
            lambda match: os.environ.get(
                match.group("braced") or match.group("bare"),
                file_values.get(match.group("braced") or match.group("bare"), match.group(0)),
            ),
            expanded,
        )
        if next_value == expanded:
            break
        expanded = next_value
    return expanded


def _load_runtime_env() -> str | None:
    if all(os.environ.get(key) for key in RUNTIME_ENV_KEYS):
        return "process"

    candidates = []
    configured_path = os.environ.get("ELMS_BROWSER_ENV_FILE")
    if configured_path:
        candidates.append(Path(configured_path).expanduser())
    candidates.extend((ROOT / "docker" / ".env.dev", ROOT / ".env"))

    seen = set()
    for candidate in candidates:
        candidate = candidate if candidate.is_absolute() else ROOT / candidate
        candidate = candidate.resolve()
        if candidate in seen or not candidate.is_file():
            continue
        seen.add(candidate)
        file_values: dict[str, str] = {}
        for raw_line in candidate.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[7:].lstrip()
            key, separator, raw_value = line.partition("=")
            if separator:
                values = shlex.split(raw_value.strip(), comments=True)
                if values:
                    file_values[key.strip()] = values[0]
        for key in RUNTIME_ENV_KEYS:
            if os.environ.get(key) or key not in file_values:
                continue
            os.environ[key] = _expand_env_references(file_values[key], file_values)
        if all(os.environ.get(key) for key in RUNTIME_ENV_KEYS):
            try:
                return str(candidate.relative_to(ROOT))
            except ValueError:
                return str(candidate)
    return None


def _method_name(url: str) -> str | None:
    marker = "/api/method/"
    if marker not in url:
        return None
    return url.split(marker, 1)[1].split("?", 1)[0]


def _app_session_reached(page) -> bool:
    try:
        return bool(page.evaluate("() => window.location.pathname.startsWith('/app')"))
    except Exception:
        try:
            from urllib.parse import urlparse

            return urlparse(page.url or "").path.startswith("/app")
        except Exception:
            return False


def _record_admission_response(response, requests: list[dict]) -> None:
    method = _method_name(response.url)
    if not method or "admission.import_api" not in method:
        return
    entry = {"method": method, "status": response.status}
    try:
        payload = response.json()
        message = payload.get("message") if isinstance(payload, dict) else None
        if isinstance(message, dict):
            for key in ("name", "status", "total_rows", "row_count"):
                if key in message:
                    entry[key] = message[key]
            if method.endswith("reveal_credential"):
                entry["invite_token_present"] = bool(message.get("invite_token"))
    except Exception:
        entry["json"] = False
    requests.append(entry)


def _api_request(requests: list[dict], suffix: str) -> dict | None:
    matches = [entry for entry in requests if entry["method"].endswith(suffix)]
    return matches[-1] if matches else None


def _response_observation(response) -> dict:
    observed = {"status": response.status}
    try:
        payload = response.json()
    except Exception:
        return observed
    if not isinstance(payload, dict):
        return observed
    message = payload.get("message")
    if isinstance(message, str):
        observed["message"] = message
    if payload.get("_server_messages"):
        observed["server_messages_present"] = True
    return observed


ADMISSION_PROVIDER_API_KEY = "elms-admission-browser-qa-v1"
ADMISSION_PROVIDER_MODEL = "elms-admission-parser-v1"


def _start_admission_test_provider() -> tuple[ThreadingHTTPServer, Thread, str]:
    class AdmissionProviderHandler(BaseHTTPRequestHandler):
        def _send_json(self, status: int, payload: dict) -> None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:
            if self.path == "/v1/models":
                self._send_json(
                    200,
                    {"object": "list", "data": [{"id": ADMISSION_PROVIDER_MODEL, "object": "model"}]},
                )
                return
            self._send_json(404, {"error": {"message": "Not found"}})

        def do_POST(self) -> None:
            if self.path != "/v1/chat/completions":
                self._send_json(404, {"error": {"message": "Not found"}})
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                request = json.loads(self.rfile.read(length).decode("utf-8"))
                messages = request.get("messages") or []
                prompt = json.loads(messages[-1]["content"])
                response = {
                    "schema_version": "admission-xlsx-v1",
                    "header": prompt.get("header") or {},
                    "rows": prompt.get("rows") or [],
                }
            except (KeyError, TypeError, ValueError, json.JSONDecodeError):
                self._send_json(400, {"error": {"message": "Invalid admission parser request"}})
                return
            self._send_json(
                200,
                {
                    "id": "elms-admission-browser-qa",
                    "object": "chat.completion",
                    "choices": [
                        {
                            "index": 0,
                            "message": {"role": "assistant", "content": json.dumps(response, ensure_ascii=False)},
                            "finish_reason": "stop",
                        }
                    ],
                },
            )

        def log_message(self, _format: str, *_args) -> None:
            return

    server = ThreadingHTTPServer(("0.0.0.0", 0), AdmissionProviderHandler)
    thread = Thread(target=server.serve_forever, name="elms-admission-browser-provider", daemon=True)
    thread.start()
    return server, thread, f"http://host.docker.internal:{server.server_port}/v1"


def _configure_admission_test_provider(page, base_url: str) -> dict:
    return page.evaluate(
        """
        async ({baseUrl, apiKey, model}) => {
            const invoke = (method, args) => new Promise((resolve) => {
                frappe.call({
                    method,
                    args,
                    callback: (response) => resolve({ok: true, message: response && response.message}),
                    error: (error) => resolve({ok: false, error: (error && (error.message || error.exception)) || "request failed"}),
                });
            });
            const context = await invoke("elms.access.api.get_company_access_context", {});
            const organization = context.ok && context.message && context.message.organization;
            if (!organization) {
                return {ok: false, error: (context.error || "Company Admin organization is not resolved")};
            }
            const saved = await invoke("elms.integrations.api.save_organization_integration", {
                organization,
                integration_type: "LLM",
                enabled: 1,
                base_url: baseUrl,
                default_model: model,
                api_key: apiKey,
            });
            if (!saved.ok || !saved.message || saved.message.organization !== organization || saved.message.integration_type !== "LLM") {
                return {ok: false, organization, error: saved.error || "LLM integration was not saved"};
            }
            return {ok: true, organization, integration_type: saved.message.integration_type, enabled: saved.message.enabled};
        }
        """,
        {"baseUrl": base_url, "apiKey": ADMISSION_PROVIDER_API_KEY, "model": ADMISSION_PROVIDER_MODEL},
    )


def _invalid_admission_fixture(valid_fixture: Path) -> dict[str, object]:
    """Return an in-memory copy of the valid workbook with one invalid row value."""

    with ZipFile(valid_fixture) as source:
        entries = {name: source.read(name) for name in source.namelist()}
    shared_strings = entries.get("xl/sharedStrings.xml", b"")
    marker = b"<t>125-609-984 78</t>"
    if marker not in shared_strings:
        raise RuntimeError("Valid admission fixture does not contain the expected SNILS value")
    entries["xl/sharedStrings.xml"] = shared_strings.replace(marker, b"<t>123</t>", 1)

    workbook = BytesIO()
    with ZipFile(workbook, "w", compression=ZIP_DEFLATED) as target:
        for name, content in entries.items():
            target.writestr(name, content)
    return {
        "name": "admission-invalid-row.xlsx",
        "mimeType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "buffer": workbook.getvalue(),
    }


def _run_admission_wire(page, base_url: str, results: dict) -> bool:
    admission_url = f"{base_url.rstrip('/')}/app/elms-admission"
    fixture_dir = ROOT / "memory-bank" / "app" / "clarify" / "fixtures-20261116-admission"
    valid_fixture = fixture_dir / "sample-rpo-smetanin.xlsx"
    invalid_fixture = _invalid_admission_fixture(valid_fixture)
    journey = {
        "journey_id": "JRN-A11-ADMISSION-IMPORT",
        "name": "Authenticated Company Admin admission upload, preview/errors, export, and one-time reveal",
        "url": admission_url,
        "status": "fail",
        "checks": [],
        "api_requests": [],
        "console_errors": [],
        "request_failures": [],
        "errors": [],
    }
    requests = journey["api_requests"]

    def on_console(message) -> None:
        if message.type == "error":
            journey["console_errors"].append(message.text)

    def on_request_failed(request) -> None:
        journey["request_failures"].append({"url": request.url, "failure": request.failure})

    page.on("response", lambda response: _record_admission_response(response, requests))
    page.on("console", on_console)
    page.on("requestfailed", on_request_failed)

    def check(name: str, passed: bool, observed) -> None:
        journey["checks"].append({"name": name, "status": "pass" if passed else "fail", "observed": observed})
        if not passed:
            journey["errors"].append(f"{name}: {observed}")

    def upload_fixture(path: Path | dict[str, object], new_revision: bool) -> dict:
        if isinstance(path, Path):
            if not path.is_file():
                raise RuntimeError(f"Fixture is missing: {path}")
            file_payload: str | dict[str, object] = str(path)
        else:
            file_payload = path
        file_input = page.locator("[data-admission-import-file]")
        file_input.set_input_files(file_payload)
        revision = page.locator("[data-admission-new-revision]")
        if revision.is_checked() != new_revision:
            revision.check() if new_revision else revision.uncheck()
        page.locator("[data-admission-import-form] button[type='submit']").click()
        page.wait_for_selector("[data-admission-import-result]", state="visible", timeout=90000)
        page.wait_for_timeout(250)
        states = page.locator("[data-admission-import-rows] .elms-admission-row-state").all_text_contents()
        errors = page.locator("[data-admission-import-rows] td:nth-child(5) small").all_text_contents()
        status_node = page.locator("[data-admission-import-status]")
        return {
            "status_text": status_node.text_content() or "",
            "status_class": status_node.get_attribute("class") or "",
            "row_states": states,
            "row_errors": [value.strip() for value in errors if value.strip()],
        }

    try:
        page.goto(admission_url, timeout=30000, wait_until="networkidle")
        page.wait_for_selector("[data-admission-import]", state="visible", timeout=30000)
        roles = page.evaluate("() => (window.frappe && Array.isArray(window.frappe.user_roles)) ? window.frappe.user_roles : []")
        check("company_admin_role_present", "ELMS Company Admin" in roles, roles)
        check("admission_import_surface_loaded", True, page.url)

        invalid_preview = upload_fixture(invalid_fixture, True)
        invalid_response = _api_request(requests, "upload_import")
        invalid_inspect = _api_request(requests, "inspect_import")
        invalid_explicit = (
            invalid_preview["status_class"].endswith("is-error")
            and invalid_preview["row_states"] == ["invalid"]
            and bool(invalid_preview["row_errors"])
        )
        check(
            "preview_errors_are_explicit",
            bool(invalid_response and invalid_response["status"] == "failed")
            and bool(invalid_inspect and invalid_inspect["status"] == "failed")
            and bool(invalid_explicit),
            invalid_preview,
        )

        valid_preview = upload_fixture(valid_fixture, True)
        valid_upload = _api_request(requests, "upload_import")
        valid_inspect = _api_request(requests, "inspect_import")
        parsed = bool(
            valid_inspect
            and valid_inspect.get("status") == "parsed"
            and valid_preview["status_class"].endswith("is-success")
            and valid_preview["row_states"] == ["valid"]
            and not valid_preview["row_errors"]
        )
        check(
            "parsed_preview_loaded",
            bool(valid_upload and valid_upload["status"] == "parsed")
            and bool(valid_inspect and valid_inspect["status"] == "parsed")
            and parsed,
            valid_preview,
        )

        export_button = page.locator("[data-admission-import-export]")
        export_button.click()
        page.wait_for_timeout(500)
        export_response = _api_request(requests, "export_import")
        check("validated_rows_exported", bool(export_response and export_response["status"] == 200), export_response)

        reveal_button = page.locator("[data-admission-reveal]").first
        reveal_present = reveal_button.count() == 1
        if reveal_present:
            reveal_button.click()
            page.wait_for_timeout(500)
        reveal_response = _api_request(requests, "reveal_credential")
        token = page.locator("[data-admission-token]").first
        token_text = token.text_content() if token.count() == 1 else ""
        reveal_success = bool(
            reveal_response
            and reveal_response["status"] == 200
            and reveal_response.get("invite_token_present")
            and token_text.strip()
            and page.locator("[data-admission-reveal]").count() == 0
        )
        check(
            "one_time_credential_reveal_audited",
            reveal_present and reveal_success,
            {
                "reveal_button_present": reveal_present,
                "token_rendered": bool(token_text.strip()),
                "reveal_button_removed": page.locator("[data-admission-reveal]").count() == 0,
                "response": reveal_response,
            },
        )
        check("browser_runtime_errors_absent", not journey["console_errors"] and not journey["request_failures"], {"console_errors": journey["console_errors"], "request_failures": journey["request_failures"]})
        journey["status"] = "pass" if not journey["errors"] else "fail"
        return journey["status"] == "pass"
    except Exception as exc:
        journey["errors"].append(str(exc))
        return False
    finally:
        results.setdefault("journeys", []).append(journey)


def run_browser_checks(base_url: str, smoke_only: bool = False) -> dict:
    from playwright.sync_api import sync_playwright

    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    runtime_env_source = _load_runtime_env()
    provider_server = None
    provider_thread = None
    provider_base_url = None
    provider_server, provider_thread, provider_base_url = _start_admission_test_provider()
    executable_path = os.environ.get(
        "PLAYWRIGHT_CHROME_EXECUTABLE",
        "/home/aero/.cache/ms-playwright/chromium_headless_shell-1248/chrome-headless-shell-linux64/chrome-headless-shell",
    )

    results = {
        "schema": "browser-qa-trace/v1",
        "base_url": base_url,
        "checks": [],
        "passed": True,
        "errors": [],
    }
    runtime_ready = all(os.environ.get(key) for key in RUNTIME_ENV_KEYS)
    results["runtime_activation"] = {
        "status": "pass" if runtime_ready else "fail",
        "source": runtime_env_source,
        "username_present": bool(os.environ.get("ELMS_BROWSER_TEST_USERNAME")),
        "password_present": bool(os.environ.get("ELMS_BROWSER_TEST_PASSWORD")),
        "role": "ELMS Company Admin",
    }
    if not runtime_ready:
        results["passed"] = False
        results["errors"].append(
            "Company Admin browser activation is unavailable; set ELMS_BROWSER_TEST_USERNAME/PASSWORD "
            "or provide ELMS_BROWSER_ENV_FILE"
        )

    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=executable_path if Path(executable_path).exists() else None,
            headless=True,
        )
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()
        auth_responses = []

        def record_auth_response(response) -> None:
            if _method_name(response.url) == "elms.sso.login.login_with_keycloak":
                auth_responses.append(response)

        page.on("response", record_auth_response)
        try:
            # 1. Navigate to login
            login_url = f"{base_url.rstrip('/')}/login"
            response = page.goto(login_url, timeout=15000, wait_until="networkidle")
            status_code = response.status if response else 0

            check_status = {
                "name": "login_page_status_200",
                "status": "pass" if status_code == 200 else "fail",
                "observed": status_code,
            }
            results["checks"].append(check_status)
            if status_code != 200:
                results["passed"] = False
                results["errors"].append(f"HTTP status is {status_code}, expected 200")

            # 2. Check title
            title = page.title()
            check_title = {
                "name": "login_page_title",
                "status": "pass" if "Login" in title else "fail",
                "observed": title,
            }
            results["checks"].append(check_title)
            if "Login" not in title:
                results["passed"] = False
                results["errors"].append(f"Title is '{title}', expected to contain 'Login'")

            # 3. Check ELMS branding in the standard Frappe login heading
            heading = page.locator(".for-login .page-card-head h4").first.text_content() or ""
            has_elms_brand = "elms" in heading.lower()
            check_branding = {
                "name": "login_heading_uses_elms_brand",
                "status": "pass" if has_elms_brand else "fail",
                "observed": heading.strip(),
            }
            results["checks"].append(check_branding)
            if not has_elms_brand:
                results["passed"] = False
                results["errors"].append(
                    f"Login heading is '{heading.strip()}', expected it to contain the ELMS brand"
                )

            # 4. Check CSS link in DOM
            links = page.evaluate("() => Array.from(document.querySelectorAll('link[rel=\"stylesheet\"]')).map(l => l.href)")
            has_login_css = any("login.css" in l for l in links)
            check_css = {
                "name": "login_css_asset_linked",
                "status": "pass" if has_login_css else "fail",
                "observed": [l for l in links if "login" in l or "elms" in l],
            }
            results["checks"].append(check_css)
            if not has_login_css:
                results["passed"] = False
                results["errors"].append("login.css asset is not linked in <head>")

            stylesheet_statuses = page.evaluate(
                """async (stylesheet_links) => {
                    const statuses = {};
                    await Promise.all(stylesheet_links.map(async (link) => {
                        try {
                            const response = await fetch(link, {cache: "no-store"});
                            statuses[link] = {
                                status: response.status,
                                content_type: response.headers.get("content-type") || ""
                            };
                        } catch (error) {
                            statuses[link] = {status: null, content_type: ""};
                        }
                    }));
                    return statuses;
                }""",
                links,
            )
            failed_stylesheets = {
                link: status
                for link, status in stylesheet_statuses.items()
                if status["status"] != 200 or "text/css" not in status["content_type"]
            }
            results["stylesheet_statuses"] = stylesheet_statuses
            check_css_delivery = {
                "name": "linked_stylesheets_are_available",
                "status": "pass" if not failed_stylesheets else "fail",
                "observed": failed_stylesheets or stylesheet_statuses,
            }
            results["checks"].append(check_css_delivery)
            if failed_stylesheets:
                results["passed"] = False
                results["errors"].append(
                    "Stylesheet requests failed: "
                    + ", ".join(f"{url} -> {status}" for url, status in failed_stylesheets.items())
                )

            # 5. Check the complete standard Frappe login surface (AC-002)
            def computed_style(selector):
                element = page.query_selector(selector)
                if not element:
                    return None
                return page.evaluate(
                    """(el) => {
                        const s = window.getComputedStyle(el);
                        return {
                            height: s.height,
                            borderRadius: s.borderRadius,
                            backgroundColor: s.backgroundColor,
                            borderColor: s.borderColor,
                            color: s.color,
                            fontFamily: s.fontFamily
                        };
                    }""",
                    element,
                )

            surface_styles = {
                "body": computed_style('body[data-path="login"]'),
                "card": computed_style(".for-login .login-content.page-card"),
                "input": computed_style(".for-login .form-control"),
                "primary_button": computed_style(".for-login .btn-login"),
                "email_link": computed_style(".for-login .btn-login-with-email-link"),
            }
            results["surface_styles"] = surface_styles
            surface_expectations = {
                "body": {"backgroundColor": "rgb(245, 247, 250)"},
                "card": {"borderRadius": "3px"},
                "input": {"height": "44px", "borderRadius": "3px"},
                "primary_button": {
                    "height": "44px",
                    "borderRadius": "3px",
                    "backgroundColor": "rgb(13, 76, 211)",
                },
            }
            surface_errors = []
            for name, expectations in surface_expectations.items():
                style = surface_styles[name]
                if style is None:
                    surface_errors.append(f"{name} element is missing")
                else:
                    for property_name, expected_value in expectations.items():
                        if style.get(property_name) != expected_value:
                            surface_errors.append(
                                f"{name}.{property_name}={style.get(property_name)!r}, expected {expected_value!r}"
                            )
            check_surface = {
                "name": "login_surface_neftegaz_contract",
                "status": "pass" if not surface_errors else "fail",
                "observed": surface_styles,
            }
            results["checks"].append(check_surface)
            if surface_errors:
                results["passed"] = False
                results["errors"].extend(surface_errors)

            check_email_link = {
                "name": "email_link_login_path_absent",
                "status": "pass" if surface_styles["email_link"] is None else "fail",
                "observed": surface_styles["email_link"],
            }
            results["checks"].append(check_email_link)
            if surface_styles["email_link"] is not None:
                results["passed"] = False
                results["errors"].append("Email-link login path is present, but ELMS uses Keycloak-only password login")

            # 6. Check the standard form is the only Keycloak entrypoint
            login_form = page.locator(".for-login form.form-login").first
            login_button = page.locator(".for-login .btn-login").first
            has_form = login_form.count() == 1 and login_button.count() == 1
            check_form = {
                "name": "standard_login_form_present",
                "status": "pass" if has_form else "fail",
                "observed": {"forms": login_form.count(), "buttons": login_button.count()},
            }
            results["checks"].append(check_form)
            if not has_form:
                results["passed"] = False
                results["errors"].append("Standard .form-login with .btn-login is missing")

            script_links = page.evaluate(
                "() => Array.from(document.querySelectorAll('script[src]')).map(script => script.src)"
            )
            has_login_js = any("login-keycloak.js" in link for link in script_links)
            check_login_js = {
                "name": "keycloak_login_js_asset_linked",
                "status": "pass" if has_login_js else "fail",
                "observed": [link for link in script_links if "login" in link or "elms" in link],
            }
            results["checks"].append(check_login_js)
            if not has_login_js:
                results["passed"] = False
                results["errors"].append("login-keycloak.js is not linked on the login page")

            # 7. Password form is the sole Keycloak path; OAuth Keycloak button must be absent
            keycloak_buttons = page.query_selector_all(".btn-keycloak")
            visible_keycloak = []
            for btn in keycloak_buttons:
                try:
                    if btn.is_visible():
                        visible_keycloak.append(btn)
                except Exception:
                    visible_keycloak.append(btn)
            has_no_oauth_btn = len(visible_keycloak) == 0
            check_btn = {
                "name": "btn_keycloak_absent",
                "status": "pass" if has_no_oauth_btn else "fail",
                "observed": len(visible_keycloak),
            }
            results["checks"].append(check_btn)
            if not has_no_oauth_btn:
                results["passed"] = False
                results["errors"].append(
                    f"Expected no visible .btn-keycloak button, found {len(visible_keycloak)}"
                )

            # Check no Yandex button
            yandex_btn = page.query_selector(".btn-yandex")
            has_no_yandex = yandex_btn is None
            check_yandex = {
                "name": "no_direct_yandex_button",
                "status": "pass" if has_no_yandex else "fail",
            }
            results["checks"].append(check_yandex)
            if not has_no_yandex:
                results["passed"] = False
                results["errors"].append("Direct Yandex button found on login page, forbidden")

            login_btn_el = page.query_selector(".for-login .btn-login")
            if login_btn_el:
                computed = page.evaluate(
                    """(el) => {
                        const s = window.getComputedStyle(el);
                        return {
                            height: s.height,
                            borderRadius: s.borderRadius,
                            backgroundColor: s.backgroundColor,
                            color: s.color,
                            display: s.display,
                            minHeight: s.minHeight
                        };
                    }""",
                    login_btn_el,
                )
                results["computed_style"] = computed

                height_ok = computed.get("height") == "44px"
                radius_ok = computed.get("borderRadius") == "3px"
                bg_ok = computed.get("backgroundColor") in ("rgb(13, 76, 211)", "#0d4cd3")

                check_geom = {
                    "name": "btn_geometry_44px_3px",
                    "status": "pass" if (height_ok and radius_ok) else "fail",
                    "observed": {"height": computed.get("height"), "borderRadius": computed.get("borderRadius")},
                }
                results["checks"].append(check_geom)
                if not (height_ok and radius_ok):
                    results["passed"] = False
                    results["errors"].append(
                        f"Button geometry mismatch: height={computed.get('height')} (expected 44px), "
                        f"borderRadius={computed.get('borderRadius')} (expected 3px)"
                    )

                check_color = {
                    "name": "btn_color_cobalt_action",
                    "status": "pass" if bg_ok else "fail",
                    "observed": {"backgroundColor": computed.get("backgroundColor"), "color": computed.get("color")},
                }
                results["checks"].append(check_color)
                if not bg_ok:
                    results["passed"] = False
                    results["errors"].append(
                        f"Button background color mismatch: {computed.get('backgroundColor')} "
                        f"(expected rgb(13, 76, 211) / #0d4cd3), overridden by login.bundle.css"
                    )

            if has_form:
                login_form.locator("#login_email").fill("elms.qa.invalid@example.test")
                login_form.locator("#login_password").fill("invalid-password")
                login_button.click()
                page.wait_for_timeout(1000)
                invalid_state = (
                    page.locator(".login-content.invalid-login").count() > 0
                    or page.locator(".for-login .page-card-body.invalid").count() > 0
                )
                check_invalid = {
                    "name": "invalid_credentials_stay_on_login",
                    "status": "pass" if invalid_state else "fail",
                    "observed": {"url": page.url, "invalid_state": invalid_state},
                }
                results["checks"].append(check_invalid)
                if not invalid_state:
                    results["passed"] = False
                    results["errors"].append("Invalid Keycloak credentials did not mark the login form invalid")

            test_username = os.environ.get("ELMS_BROWSER_TEST_USERNAME")
            test_password = os.environ.get("ELMS_BROWSER_TEST_PASSWORD")
            if test_username and test_password:
                page.goto(login_url, timeout=15000, wait_until="networkidle")
                page.wait_for_timeout(500)
                login_form = page.locator(".for-login form.form-login").first
                login_form.locator("#login_email").fill(test_username)
                login_form.locator("#login_password").fill(test_password)
                auth_response = None
                auth_observation = None
                auth_wait_error = None
                success = False
                try:
                    with page.expect_response(
                        lambda response: _method_name(response.url) == "elms.sso.login.login_with_keycloak",
                        timeout=15000,
                    ) as response_info:
                        login_form.locator(".btn-login").click()
                    auth_response = response_info.value
                    auth_observation = _response_observation(auth_response)
                    if auth_response.status == 200:
                        page.wait_for_function(
                            "() => window.location.pathname.startsWith('/app')",
                            timeout=20000,
                        )
                        success = _app_session_reached(page)
                    else:
                        success = False
                except Exception as exc:
                    auth_wait_error = type(exc).__name__
                    if auth_responses:
                        auth_response = auth_responses[-1]
                        auth_observation = _response_observation(auth_response)
                    try:
                        page.wait_for_function(
                            "() => window.location.pathname.startsWith('/app')",
                            timeout=10000,
                        )
                    except Exception:
                        pass
                    if auth_response is not None and auth_response.status == 200 and _app_session_reached(page):
                        success = True
                    elif _app_session_reached(page):
                        success = True
                check_success = {
                    "name": "valid_keycloak_credentials_reach_app",
                    "status": "pass" if success else "fail",
                    "observed": {
                        "url": page.url,
                        "auth": auth_observation,
                        "wait_error": auth_wait_error,
                        "app_session": _app_session_reached(page),
                    },
                }
                results["checks"].append(check_success)
                if success:
                    results["runtime_activation"]["authenticated"] = True
                else:
                    auth_status = auth_response.status if auth_response else None
                    blocker = (
                        "Company Admin authentication did not establish an /app session; "
                        "elms.sso.login.login_with_keycloak returned "
                        f"HTTP {auth_status if auth_status is not None else 'no response'}."
                    )
                    if auth_status == 417:
                        blocker += " Frappe rejected the Keycloak token exchange as invalid credentials."
                    results["runtime_activation"].update(
                        {
                            "status": "blocked",
                            "authenticated": False,
                            "blocker": blocker,
                        }
                    )
                    results["passed"] = False
                    results["errors"].append(blocker)
                    results["journeys"] = [
                        {
                            "journey_id": "JRN-A11-ADMISSION-IMPORT",
                            "name": "Authenticated Company Admin admission upload, preview/errors, export, and one-time reveal",
                            "url": f"{base_url.rstrip('/')}/app/elms-admission",
                            "status": "blocked",
                            "errors": [blocker],
                        }
                    ]
                if success:
                    provider_setup = {"ok": False, "error": "Admission test provider is unavailable"}
                    try:
                        provider_setup = _configure_admission_test_provider(page, provider_base_url)
                    except Exception as exc:
                        provider_setup = {"ok": False, "error": f"Admission test provider setup failed: {exc}"}
                    results["admission_provider"] = {
                        "status": "pass" if provider_setup.get("ok") else "fail",
                        "base_url": provider_base_url,
                        "model": ADMISSION_PROVIDER_MODEL,
                        "organization": provider_setup.get("organization"),
                    }
                    provider_check = {
                        "name": "admission_test_provider_configured",
                        "status": "pass" if provider_setup.get("ok") else "fail",
                        "observed": results["admission_provider"],
                    }
                    results["checks"].append(provider_check)
                    if provider_setup.get("ok"):
                        if not _run_admission_wire(page, base_url, results):
                            results["passed"] = False
                    else:
                        results["passed"] = False
                        results["errors"].append(str(provider_setup.get("error") or "Admission test provider setup failed"))
                        results["journeys"] = [
                            {
                                "journey_id": "JRN-A11-ADMISSION-IMPORT",
                                "name": "Authenticated Company Admin admission upload, preview/errors, export, and one-time reveal",
                                "url": f"{base_url.rstrip('/')}/app/elms-admission",
                                "status": "blocked",
                                "errors": [str(provider_setup.get("error") or "Admission test provider setup failed")],
                            }
                        ]
            else:
                results["journeys"] = [
                    {
                        "journey_id": "JRN-A11-ADMISSION-IMPORT",
                        "name": "Authenticated Company Admin admission upload, preview/errors, export, and one-time reveal",
                        "url": f"{base_url.rstrip('/')}/app/elms-admission",
                        "status": "blocked",
                        "errors": ["Company Admin credentials are unavailable to the browser process"],
                    }
                ]

        finally:
            browser.close()
            if provider_server is not None:
                provider_server.shutdown()
                provider_server.server_close()
            if provider_thread is not None:
                provider_thread.join(timeout=2)

    evidence_file = ARTIFACTS_DIR / "browser-evidence.json"
    results.update(
        {
            "status": "pass" if results["passed"] else "fail",
            "evidence_type": "runtime_browser",
            "live_evidence": True,
            "timestamp": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "command": (
                "NEFTEGAZ_BROWSER=chromium timeout -k 10s 300s .venv/bin/python "
                "scripts/run_browser_qa.py --smoke-only"
                if smoke_only
                else "NEFTEGAZ_BROWSER=chromium timeout -k 10s 300s .venv/bin/python scripts/run_browser_qa.py"
            ),
            "exit_code": 0 if results["passed"] else 1,
        }
    )
    evidence_file.write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return results


def main():
    parser = argparse.ArgumentParser(description="Run browser QA tests.")
    parser.add_argument("--base-url", default="http://elms.localhost:8082", help="Base URL")
    parser.add_argument("--smoke-only", action="store_true", help="Run smoke checks only")
    args = parser.parse_args()

    results = run_browser_checks(args.base_url, smoke_only=args.smoke_only)
    print(json.dumps(results, indent=2, ensure_ascii=False))

    if not results["passed"]:
        print("\nBrowser QA FAILED with errors:", file=sys.stderr)
        for err in results["errors"]:
            print(f"  - {err}", file=sys.stderr)
        sys.exit(1)
    else:
        print("\nBrowser QA PASSED", file=sys.stdout)
        sys.exit(0)


if __name__ == "__main__":
    main()
