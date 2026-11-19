#!/usr/bin/env python3
"""Run automated browser QA tests for ELMS Keycloak Login UI via Playwright."""

from __future__ import annotations

import argparse
import base64
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
from time import monotonic
from urllib.parse import quote
from xml.etree import ElementTree
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parent.parent
ARTIFACTS_DIR = ROOT / "browser-artifacts"
RUNTIME_ENV_KEYS = ("ELMS_BROWSER_TEST_USERNAME", "ELMS_BROWSER_TEST_PASSWORD")
OPTIONAL_BROWSER_ENV_KEYS = ("KEYCLOAK_TEST_ADMIN_PASSWORD",)
ENV_REFERENCE = re.compile(r"\$(?:\{(?P<braced>[A-Za-z_][A-Za-z0-9_]*)\}|(?P<bare>[A-Za-z_][A-Za-z0-9_]*))")
LOGIN_READY_SELECTOR = ".for-login .page-card-head h4"
LOGIN_NAVIGATION_TIMEOUT_MS = 30000
LOGIN_READINESS_TIMEOUT_MS = 20000
LOGIN_READINESS_ATTEMPTS = 3
LOGIN_READINESS_RETRY_DELAY_MS = 500
LOGIN_WAIT_UNTIL = "domcontentloaded"


class LoginReadinessError(RuntimeError):
    """Raised when the login page does not expose its real ready marker in time."""


def _login_selector_present(page) -> bool:
    try:
        return page.locator(LOGIN_READY_SELECTOR).count() > 0
    except Exception:
        return False


def _navigate_to_login(page, login_url: str):
    last_error = None
    response = None

    for attempt in range(1, LOGIN_READINESS_ATTEMPTS + 1):
        try:
            if attempt == 1:
                response = page.goto(
                    login_url,
                    timeout=LOGIN_NAVIGATION_TIMEOUT_MS,
                    wait_until=LOGIN_WAIT_UNTIL,
                )
            else:
                response = page.reload(
                    timeout=LOGIN_NAVIGATION_TIMEOUT_MS,
                    wait_until=LOGIN_WAIT_UNTIL,
                )
        except Exception as exc:
            last_error = exc

        try:
            page.locator(LOGIN_READY_SELECTOR).first.wait_for(
                state="visible",
                timeout=LOGIN_READINESS_TIMEOUT_MS,
            )
            return response
        except Exception as exc:
            last_error = exc
            if attempt < LOGIN_READINESS_ATTEMPTS:
                page.wait_for_timeout(LOGIN_READINESS_RETRY_DELAY_MS)

    detail = "unknown error"
    if last_error is not None:
        detail = f"{type(last_error).__name__}: {str(last_error).splitlines()[0]}"
    raise LoginReadinessError(
        f"Login page readiness was not achieved after {LOGIN_READINESS_ATTEMPTS} bounded "
        f"attempts for {LOGIN_READY_SELECTOR!r}; the page-ready selector remained "
        f"unavailable. Last probe error: {detail}"
    ) from last_error


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
        for key in RUNTIME_ENV_KEYS + OPTIONAL_BROWSER_ENV_KEYS:
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


def _is_post_response(response, method: str) -> bool:
    return response.request.method == "POST" and _method_name(response.url) == method


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
    tracked = method and (
        "admission.import_api" in method
        or method.endswith("elms.lms.api.admission.preview_admission_import")
        or method.endswith("elms.lms.api.admission.confirm_admission_import")
    )
    if not tracked:
        return
    entry = {"method": method, "status": response.status, "http_status": response.status}
    try:
        payload = response.json()
        message = payload.get("message") if isinstance(payload, dict) else None
        if isinstance(message, dict):
            for key in (
                "name",
                "status",
                "ok",
                "import_id",
                "total_rows",
                "row_count",
                "selected_count",
                "enrolled_count",
                "remaining_seats",
            ):
                if key in message:
                    entry[key] = message[key]
            enrolled_rows = message.get("enrolled_rows")
            if isinstance(enrolled_rows, list):
                entry["enrolled_statuses"] = [
                    row.get("status") for row in enrolled_rows if isinstance(row, dict)
                ]
            errors = message.get("errors")
            if isinstance(errors, list):
                entry["error_codes"] = [
                    error.get("code") for error in errors if isinstance(error, dict)
                ]
            if method.endswith("reveal_credential"):
                entry["invite_token_present"] = bool(message.get("invite_token"))
    except Exception:
        entry["json"] = False
    requests.append(entry)


def _api_request(requests: list[dict], suffix: str) -> dict | None:
    matches = [entry for entry in requests if entry["method"].endswith(suffix)]
    return matches[-1] if matches else None


def _attach_latest_active_subscription(
    page,
    import_id: str,
    preferred_subscription_id: str | None = None,
    preferred_course_id: str | None = None,
) -> dict:
    """Bind the parsed import to the scoped active quota used by this wire run."""

    return page.evaluate(
        """
        async ({importId, preferredSubscriptionId, preferredCourseId}) => {
            const invoke = (method, args) => new Promise((resolve) => {
                frappe.call({
                    method,
                    args,
                    callback: (response) => resolve({ok: true, message: response && response.message}),
                    error: (error) => resolve({ok: false, error: (error && (error.message || error.exception)) || "request failed"}),
                });
            });
            const imported = await invoke("frappe.client.get", {
                doctype: "ELMS Admission Import",
                name: importId,
            });
            const importDoc = imported.ok && imported.message;
            if (!importDoc || !importDoc.organization) {
                return {ok: false, error: imported.error || "Parsed import organization is unavailable"};
            }

            const snapshot = await invoke("elms.lms.api.get_learning_admin_data", {});
            const subscriptions = snapshot.ok && snapshot.message && Array.isArray(snapshot.message.subscriptions)
                ? snapshot.message.subscriptions
                : [];
            const active = subscriptions.filter((row) => {
                const total = Number(row.total_seats || 0);
                const used = Number(row.seats_used || 0);
                return row.status === "Active"
                    && total > used
                    && (!preferredCourseId || row.course === preferredCourseId);
            });
            if (!active.length) {
                return {
                    ok: false,
                    organization: importDoc.organization,
                    course: preferredCourseId,
                    error: "No active Company Admin subscription with available seats linked to the prepared course",
                };
            }
            const selected = active.find((row) => row.name === preferredSubscriptionId) || active[0];
            const selectedDoc = await invoke("frappe.client.get", {
                doctype: "ELMS Subscription",
                name: selected.name,
            });
            const subscription = selectedDoc.ok && selectedDoc.message;
            const totalSeats = Number(subscription && subscription.total_seats);
            const seatsUsed = Number(subscription && subscription.seats_used);
            const availableSeats = totalSeats - seatsUsed;
            if (
                !subscription
                || subscription.organization !== importDoc.organization
                || subscription.status !== "Active"
                || !subscription.course
                || (preferredCourseId && subscription.course !== preferredCourseId)
                || !Number.isFinite(availableSeats)
                || availableSeats <= 0
            ) {
                return {
                    ok: false,
                    organization: importDoc.organization,
                    course: preferredCourseId,
                    subscription_id: selected.name,
                    error: selectedDoc.error || "Selected subscription is not an active available quota owned by the parsed import organization and prepared course",
                };
            }

            const saved = await invoke("frappe.client.set_value", {
                doctype: "ELMS Admission Import",
                name: importId,
                fieldname: "subscription_id",
                value: selected.name,
            });
            if (!saved.ok) {
                return {ok: false, organization: importDoc.organization, subscription_id: selected.name, error: saved.error || "Subscription association failed"};
            }
            const readback = await invoke("frappe.client.get", {
                doctype: "ELMS Admission Import",
                name: importId,
            });
            const persisted = readback.ok && readback.message && readback.message.subscription_id === selected.name;
            return {
                ok: Boolean(persisted),
                organization: importDoc.organization,
                course: subscription.course,
                subscription_id: selected.name,
                total_seats: totalSeats,
                seats_used: seatsUsed,
                available_seats: availableSeats,
                selection_rule: "deterministic active Company Admin subscription with available seats linked to the prepared course",
                persisted,
                error: persisted ? null : (readback.error || "Subscription association readback did not persist"),
            };
        }
        """,
        {
            "importId": import_id,
            "preferredSubscriptionId": preferred_subscription_id,
            "preferredCourseId": preferred_course_id,
        },
    )


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
B2B_WIRE_COURSE_CODE = "ELMS-T-A12-B2B-WIRE-COURSE"
B2B_WIRE_COURSE_NAME = "T-A12 B2B wire course"
B2B_WIRE_PROGRAM = "T-A12 B2B wire program"
B2B_WIRE_TRAINING_KIND = "повышение квалификации"
B2B_WIRE_BATCH_NAME = "T-A12 B2B wire batch"
B2B_WIRE_BATCH_ORDER = "T-A12-B2B-WIRE"
B2B_WIRE_SUBSCRIPTION_CONTRACT = "T-A12-B2B-WIRE"
B2B_WIRE_TOTAL_SEATS = 100
B2B_WIRE_PLATFORM_OWNER = "Демонстрационный контур НефтеГаз"
T_A13_CUSTOM_FIELD_KEY = "qa_t_a13_wire"
T_A13_CUSTOM_FIELD_LABEL = "T-A13 Browser Additional"
T_A13_CUSTOM_FIELD_VALUE = "T-A13 authenticated Course readback"
T_A14_PLATFORM_USERNAME = "elms.test.admin@elms.local"
T_A14_PLATFORM_PASSWORD_ENV = "KEYCLOAK_TEST_ADMIN_PASSWORD"
T_A11_SHARED_JOURNEY_ID = "JRN-A11-ADMISSION-IMPORT"
T_A11_SHARED_REQUEST_FAILURE_METHOD = "elms.ai.api.get_access"
T_A11_SHARED_REQUEST_FAILURE = "net::ERR_ABORTED"


def _set_ac_disposition(results: dict) -> None:
    """Keep unrelated admission coverage separate from the T-A13 AC report."""

    results["ac_disposition"] = {
        "task_id": "T-A13-elms-custom-fields-course-program-batch",
        "in_scope": [
            {
                "journey_id": "JRN-T-A13-CUSTOM-FIELDS-001",
                "area": "custom_fields",
                "disposition": "in_scope",
            }
        ],
        "out_of_scope": [
            {
                "area": "admission",
                "journey_id": "JRN-A11-ADMISSION-IMPORT",
                "disposition": "separate_provenance",
                "provenance": "independent A11 admission wire coverage retained in the shared browser harness",
                "t_a13_bugfix_impact": "none",
                "evidence": [
                    "The T-A13 journey is independently identified as JRN-T-A13-CUSTOM-FIELDS-001.",
                    "The T-A13 journey exercises only custom-field definition and Course-value save/readback checks.",
                    "Admission coverage is independently identified as JRN-A11-ADMISSION-IMPORT.",
                ],
            }
        ],
    }


def _record_t14_response(response, requests: list[dict], actor: str) -> None:
    method = _method_name(response.url)
    tracked_methods = {
        "elms.access.api.get_company_access_context",
        "elms.cabinet.api.get_org_roster",
        "elms.cabinet.api.export_org_progress",
        "elms.access.api.invite_org_user",
        "elms.admission.import_api.upload_import",
        "elms.lms.api.enroll_learner",
        "elms.lms.api.admission.confirm_admission_import",
        "frappe.client.get_list",
    }
    if method not in tracked_methods:
        return
    entry = {"actor": actor, "method": method, "status": response.status, "http_status": response.status}
    try:
        payload = response.json()
        message = payload.get("message") if isinstance(payload, dict) else None
        if method == "elms.access.api.get_company_access_context" and isinstance(message, dict):
            for key in ("organization", "organizations", "platform_viewer", "read_only", "platform_admin"):
                if key in message:
                    entry[key] = message[key]
        elif method == "elms.cabinet.api.get_org_roster" and isinstance(message, dict):
            rows = message.get("rows")
            entry.update(
                {
                    "organization": message.get("organization"),
                    "total": message.get("total"),
                    "page": message.get("page"),
                    "page_size": message.get("page_size"),
                    "row_count": len(rows) if isinstance(rows, list) else None,
                    "empty": message.get("empty"),
                }
            )
        elif method == "elms.cabinet.api.export_org_progress" and isinstance(message, dict):
            content = message.get("content_base64")
            csv_header = None
            if isinstance(content, str):
                try:
                    csv_header = base64.b64decode(content).decode("utf-8-sig").splitlines()[0]
                except (ValueError, UnicodeDecodeError, IndexError):
                    csv_header = None
            entry.update(
                {
                    "organization": message.get("organization"),
                    "filename": message.get("filename"),
                    "row_count": message.get("row_count"),
                    "charset": message.get("charset"),
                    "csv_header": csv_header,
                    "content_base64_present": bool(content),
                }
            )
        elif method == "frappe.client.get_list" and isinstance(message, list):
            entry["row_count"] = len(message)
            entry["audit_rows"] = [
                {
                    key: row.get(key)
                    for key in (
                        "name",
                        "user",
                        "organization",
                        "activity_type",
                        "reference_doctype",
                        "reference_name",
                        "timestamp",
                    )
                    if key in row
                }
                for row in message
                if isinstance(row, dict)
            ]
        if isinstance(payload, dict):
            for key in ("exc_type", "exception", "_server_messages"):
                if payload.get(key):
                    entry[key] = payload[key]
    except Exception:
        entry["json"] = False
    requests.append(entry)


def _is_declared_a11_shared_request_failure(failure: dict) -> bool:
    return (
        _method_name(str(failure.get("url") or "")) == T_A11_SHARED_REQUEST_FAILURE_METHOD
        and failure.get("failure") == T_A11_SHARED_REQUEST_FAILURE
    )


def _t14_denial_exception_texts(declaration: dict) -> tuple[str, ...]:
    observed = declaration.get("observed")
    if not isinstance(observed, dict) or observed.get("http_status") != 403:
        return ()

    texts: list[str] = []
    exception = observed.get("exception")
    if isinstance(exception, str) and exception:
        texts.append(exception)

    server_messages = observed.get("_server_messages")
    if isinstance(server_messages, str):
        try:
            server_messages = json.loads(server_messages)
        except (TypeError, ValueError):
            server_messages = []
    if isinstance(server_messages, list):
        for raw_message in server_messages:
            message = raw_message
            if isinstance(raw_message, str):
                try:
                    message = json.loads(raw_message)
                except (TypeError, ValueError):
                    message = None
            if not isinstance(message, dict):
                continue
            detail = message.get("message")
            exc_type = observed.get("exc_type")
            if isinstance(detail, str) and detail:
                texts.append(detail)
                if isinstance(exc_type, str) and exc_type:
                    texts.append(f"{exc_type}: {detail}")
    return tuple(dict.fromkeys(texts))


def _classify_t14_console_errors(
    console_errors: list[str], expected_denials: list[dict]
) -> tuple[list[str], list[str]]:
    observed_denials = [
        declaration
        for declaration in expected_denials
        if isinstance(declaration.get("observed"), dict)
        and declaration["observed"].get("http_status") == 403
    ]
    matched_tracebacks: set[int] = set()
    expected_console_errors: list[str] = []
    unexpected_console_errors: list[str] = []
    generic_403_seen = 0
    generic_403_marker = "Failed to load resource: the server responded with a status of 403"

    for message in console_errors:
        traceback_match = next(
            (
                index
                for index, declaration in enumerate(observed_denials)
                if index not in matched_tracebacks
                and any(text in message for text in _t14_denial_exception_texts(declaration))
            ),
            None,
        )
        generic_403_trace = generic_403_marker in message
        if traceback_match is not None:
            matched_tracebacks.add(traceback_match)
            expected_console_errors.append(message)
        elif generic_403_trace and generic_403_seen < len(observed_denials):
            generic_403_seen += 1
            expected_console_errors.append(message)
        else:
            unexpected_console_errors.append(message)

    return expected_console_errors, unexpected_console_errors


def _latest_t14_response(requests: list[dict], method: str, start: int = 0) -> dict | None:
    matches = [entry for entry in requests[start:] if entry.get("method") == method]
    return matches[-1] if matches else None


def _wait_for_t14_response(
    page,
    requests: list[dict],
    method: str,
    start: int = 0,
    timeout_ms: int = 10000,
) -> dict | None:
    deadline = monotonic() + timeout_ms / 1000
    while monotonic() < deadline:
        response = _latest_t14_response(requests, method, start)
        if response is not None:
            return response
        page.wait_for_timeout(50)
    return _latest_t14_response(requests, method, start)


def _call_t14(page, method: str, args: dict) -> dict:
    return page.evaluate(
        """
        async ({method, args}) => new Promise((resolve) => {
            let settled = false;
            const finish = (value) => {
                if (!settled) {
                    settled = true;
                    resolve(value);
                }
            };
            try {
                frappe.call({
                    method,
                    args,
                    callback: (response) => finish({
                        ok: true,
                        message: response && response.message,
                        exception: response && response.exception,
                    }),
                    error: (error) => finish({
                        ok: false,
                        error: (error && (error.message || error.exception)) || "request failed",
                    }),
                });
            } catch (error) {
                finish({ok: false, error: (error && error.message) || "request failed"});
            }
        })
        """,
        {"method": method, "args": args},
    )


def _run_t_a14_wire(page, browser, base_url: str, results: dict) -> bool:
    """Exercise the authenticated platform-view and Company Admin boundaries."""

    cabinet_url = f"{base_url.rstrip('/')}/app/elms-cabinet"
    journey = {
        "journey_id": "JRN-T-A14-ADMIN-ORG-VIEW-001",
        "name": "Authenticated platform organization directory, read-only selected-org view, and Company Admin continuity",
        "url": cabinet_url,
        "status": "fail",
        "checks": [],
        "api_requests": [],
        "console_errors": [],
        "request_failures": [],
        "expected_denials": [],
        "expected_console_errors": [],
        "unexpected_console_errors": [],
        "non_blocking_shared_request_failures": [],
        "errors": [],
    }
    platform_requests: list[dict] = []
    company_requests: list[dict] = []
    platform_context = None
    platform_page = None
    platform_response_handler = None
    company_response_handler = None
    platform_organizations: list[str] = []
    selected_organization = ""
    company_organization = ""

    def check(name: str, passed: bool, observed) -> None:
        journey["checks"].append({"name": name, "status": "pass" if passed else "fail", "observed": observed})
        if not passed:
            journey["errors"].append(f"{name}: {observed}")

    def on_console(message) -> None:
        if message.type == "error":
            journey["console_errors"].append(message.text)

    def on_request_failed(request) -> None:
        journey["request_failures"].append({"url": request.url, "failure": request.failure})

    def declare_expected_denial(check_name: str, actor: str, method: str) -> dict:
        declaration = {
            "check_name": check_name,
            "actor": actor,
            "method": method,
            "expected_status": 403,
        }
        journey["expected_denials"].append(declaration)
        return declaration

    try:
        platform_password = os.environ.get(T_A14_PLATFORM_PASSWORD_ENV)
        check(
            "platform_viewer_browser_activation_available",
            bool(platform_password),
            {"username": T_A14_PLATFORM_USERNAME, "password_present": bool(platform_password)},
        )
        if platform_password:
            platform_context = browser.new_context(viewport={"width": 1280, "height": 800})
            platform_page = platform_context.new_page()
            platform_response_handler = lambda response: _record_t14_response(
                response, platform_requests, "platform_viewer"
            )
            platform_page.on("response", platform_response_handler)
            platform_page.on("console", on_console)
            platform_page.on("requestfailed", on_request_failed)
            platform_auth_responses = []
            platform_page.on(
                "response",
                lambda response: platform_auth_responses.append(response)
                if _method_name(response.url) == "elms.sso.login.login_with_keycloak"
                else None,
            )
            _navigate_to_login(platform_page, f"{base_url.rstrip('/')}/login")
            login_form = platform_page.locator(".for-login form.form-login").first
            login_form.locator("#login_email").fill(T_A14_PLATFORM_USERNAME)
            login_form.locator("#login_password").fill(platform_password)
            auth_response = None
            auth_wait_error = None
            try:
                with platform_page.expect_response(
                    lambda response: _method_name(response.url) == "elms.sso.login.login_with_keycloak",
                    timeout=15000,
                ) as response_info:
                    login_form.locator(".btn-login").click()
                auth_response = response_info.value
            except Exception as exc:
                auth_wait_error = type(exc).__name__
                if platform_auth_responses:
                    auth_response = platform_auth_responses[-1]
            try:
                platform_page.wait_for_function(
                    "() => window.location.pathname.startsWith('/app')",
                    timeout=20000,
                )
            except Exception:
                pass
            platform_authenticated = _app_session_reached(platform_page)
            check(
                "platform_viewer_credentials_reach_app",
                platform_authenticated,
                {
                    "url": platform_page.url,
                    "auth": _response_observation(auth_response) if auth_response else None,
                    "wait_error": auth_wait_error,
                    "app_session": platform_authenticated,
                },
            )
            if platform_authenticated:
                results["runtime_activation"]["platform_authenticated"] = True
                role_ready = False
                try:
                    platform_page.wait_for_function(
                        """
                        () => {
                            const frappe = window.frappe;
                            const userRoles = frappe && Array.isArray(frappe.user_roles) ? frappe.user_roles : [];
                            const bootRoles = frappe && frappe.boot && frappe.boot.user && Array.isArray(frappe.boot.user.roles)
                                ? frappe.boot.user.roles
                                : [];
                            const hasRole = Boolean(
                                frappe
                                && frappe.user
                                && typeof frappe.user.has_role === "function"
                                && frappe.user.has_role("ELMS Admin")
                            );
                            return userRoles.includes("ELMS Admin") || bootRoles.includes("ELMS Admin") || hasRole;
                        }
                        """,
                        timeout=30000,
                    )
                    role_ready = True
                except Exception:
                    pass
                role_state = platform_page.evaluate(
                    """
                    ({roleReady}) => {
                        const frappe = window.frappe;
                        const userRoles = frappe && Array.isArray(frappe.user_roles) ? frappe.user_roles : [];
                        const bootRoles = frappe && frappe.boot && frappe.boot.user && Array.isArray(frappe.boot.user.roles)
                            ? frappe.boot.user.roles
                            : [];
                        const hasRole = Boolean(
                            frappe
                            && frappe.user
                            && typeof frappe.user.has_role === "function"
                            && frappe.user.has_role("ELMS Admin")
                        );
                        return {
                            user_roles: userRoles,
                            boot_roles: bootRoles,
                            has_elms_admin: hasRole,
                            role_ready: roleReady,
                        };
                    }
                    """,
                    {"roleReady": role_ready},
                )
                role_present = (
                    "ELMS Admin" in role_state.get("user_roles", [])
                    or "ELMS Admin" in role_state.get("boot_roles", [])
                    or role_state.get("has_elms_admin") is True
                )
                role_state["role_ready"] = role_ready
                check("platform_viewer_role_present", role_ready and role_present, role_state)
                context_start = len(platform_requests)
                platform_page.goto(cabinet_url, timeout=30000, wait_until="domcontentloaded")
                platform_page.wait_for_selector("[data-cabinet-organization]", state="visible", timeout=30000)
                platform_page.wait_for_function(
                    "() => document.querySelectorAll('[data-cabinet-organization] option[value]').length >= 2",
                    timeout=30000,
                )
                context_entry = _wait_for_t14_response(
                    platform_page,
                    platform_requests,
                    "elms.access.api.get_company_access_context",
                    context_start,
                )
                platform_organizations = list(context_entry.get("organizations") or []) if context_entry else []
                option_values = platform_page.locator("[data-cabinet-organization] option").evaluate_all(
                    "options => options.map(option => option.value).filter(Boolean)"
                )
                check(
                    "platform_organization_directory_is_server_backed",
                    bool(context_entry)
                    and context_entry.get("http_status") == 200
                    and context_entry.get("platform_viewer") is True
                    and context_entry.get("read_only") is True
                    and len(platform_organizations) >= 2
                    and option_values == platform_organizations,
                    {
                        "context": context_entry,
                        "options": option_values,
                    },
                )
                if platform_organizations:
                    selected_organization = platform_organizations[0]
                if selected_organization:
                    session_before = platform_page.evaluate(
                        "() => (window.frappe && window.frappe.session && window.frappe.session.user) || ''"
                    )
                    roster_start = len(platform_requests)
                    platform_page.locator("[data-cabinet-organization]").select_option(selected_organization)
                    platform_page.wait_for_function(
                        "() => { const node = document.querySelector('[data-cabinet-pill]'); return node && (node.textContent.includes('Готово') || node.textContent.includes('Пусто')); }",
                        timeout=30000,
                    )
                    roster_entry = _wait_for_t14_response(
                        platform_page,
                        platform_requests,
                        "elms.cabinet.api.get_org_roster",
                        roster_start,
                    )
                    rendered_org = platform_page.locator("[data-cabinet-org-name]").first.text_content() or ""
                    session_after_roster = platform_page.evaluate(
                        "() => (window.frappe && window.frappe.session && window.frappe.session.user) || ''"
                    )
                    check(
                        "selected_organization_roster_is_readable_and_audited",
                        bool(roster_entry)
                        and roster_entry.get("http_status") == 200
                        and roster_entry.get("organization") == selected_organization
                        and rendered_org.strip() == selected_organization
                        and session_before == session_after_roster,
                        {
                            "roster": roster_entry,
                            "rendered_organization": rendered_org.strip(),
                            "session_before": session_before,
                            "session_after": session_after_roster,
                        },
                    )
                    export_start = len(platform_requests)
                    platform_page.locator("[data-cabinet-export]").click()
                    platform_page.wait_for_function(
                        "() => { const node = document.querySelector('[data-cabinet-status]'); return node && node.textContent.includes('Выгрузка сформирована'); }",
                        timeout=30000,
                    )
                    export_entry = _wait_for_t14_response(
                        platform_page,
                        platform_requests,
                        "elms.cabinet.api.export_org_progress",
                        export_start,
                    )
                    check(
                        "selected_organization_export_is_server_generated",
                        bool(export_entry)
                        and export_entry.get("http_status") == 200
                        and export_entry.get("organization") == selected_organization
                        and export_entry.get("charset") == "UTF-8"
                        and export_entry.get("csv_header") == "user,full_name,email,user_enabled,roles,enrollments"
                        and export_entry.get("content_base64_present") is True,
                        export_entry,
                    )
                    audit_start = len(platform_requests)
                    audit_result = _call_t14(
                        platform_page,
                        "frappe.client.get_list",
                        {
                            "doctype": "ELMS User Activity",
                            "filters": {
                                "user": session_before,
                                "organization": selected_organization,
                                "activity_type": "Organization View",
                                "reference_doctype": "ELMS Organization",
                                "reference_name": selected_organization,
                            },
                            "fields": [
                                "name",
                                "user",
                                "organization",
                                "activity_type",
                                "reference_doctype",
                                "reference_name",
                                "timestamp",
                            ],
                            "order_by": "timestamp desc",
                            "limit_page_length": 5,
                        },
                    )
                    audit_entry = _wait_for_t14_response(
                        platform_page,
                        platform_requests,
                        "frappe.client.get_list",
                        audit_start,
                    )
                    check(
                        "organization_view_audit_is_persisted_in_user_activity",
                        bool(audit_entry)
                        and audit_entry.get("http_status") == 200
                        and audit_entry.get("row_count", 0) > 0,
                        {"response": audit_entry, "call": audit_result},
                    )

                    mutation_calls = (
                        (
                            "platform_invite_denied_before_write",
                            "elms.access.api.invite_org_user",
                            {
                                "email": "t-a14-denied@example.test",
                                "first_name": "T-A14",
                                "last_name": "Denied",
                                "organization": selected_organization,
                                "role_profile": "ELMS Learner Profile",
                            },
                        ),
                        (
                            "platform_import_upload_denied_before_write",
                            "elms.admission.import_api.upload_import",
                            {
                                "file_name": "t-a14-denied.xlsx",
                                "content": "AA==",
                                "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                "organization": selected_organization,
                                "new_revision": True,
                            },
                        ),
                        (
                            "platform_b2c_enrollment_denied_before_write",
                            "elms.lms.api.enroll_learner",
                            {"user": "t-a14-denied@example.test", "batch": "T-A14-DENIED-BATCH"},
                        ),
                        (
                            "platform_b2b_confirmation_denied_before_write",
                            "elms.lms.api.admission.confirm_admission_import",
                            {"import_id": "T-A14-DENIED-IMPORT"},
                        ),
                    )
                    for check_name, method, args in mutation_calls:
                        denial = declare_expected_denial(check_name, "platform_viewer", method)
                        mutation_start = len(platform_requests)
                        mutation_call = _call_t14(platform_page, method, args)
                        mutation_entry = _wait_for_t14_response(
                            platform_page,
                            platform_requests,
                            method,
                            mutation_start,
                        )
                        denial.update(
                            {
                                "observed": mutation_entry,
                                "call": mutation_call,
                                "status": "pass"
                                if mutation_entry and mutation_entry.get("http_status") == 403
                                else "fail",
                            }
                        )
                        check(
                            check_name,
                            bool(mutation_entry) and mutation_entry.get("http_status") == 403,
                            {"response": mutation_entry, "call": mutation_call},
                        )

        company_page = page
        company_response_handler = lambda response: _record_t14_response(
            response, company_requests, "company_admin"
        )
        company_page.on("response", company_response_handler)
        company_page.on("console", on_console)
        company_page.on("requestfailed", on_request_failed)
        company_context_start = len(company_requests)
        company_roster_start = len(company_requests)
        company_page.goto(cabinet_url, timeout=30000, wait_until="domcontentloaded")
        company_page.wait_for_selector("[data-cabinet-organization]", state="visible", timeout=30000)
        company_page.wait_for_function(
            "() => document.querySelectorAll('[data-cabinet-organization] option[value]').length >= 1",
            timeout=30000,
        )
        company_context = _wait_for_t14_response(
            company_page,
            company_requests,
            "elms.access.api.get_company_access_context",
            company_context_start,
        )
        company_options = company_page.locator("[data-cabinet-organization] option").evaluate_all(
            "options => options.map(option => option.value).filter(Boolean)"
        )
        company_organization = str(company_context.get("organization") or (company_options[0] if company_options else "")) if company_context else ""
        check(
            "company_admin_context_remains_own_organization_only",
            bool(company_context)
            and company_context.get("http_status") == 200
            and company_context.get("platform_viewer") is False
            and company_context.get("read_only") is False
            and len(company_options) == 1
            and company_organization == company_options[0]
            and company_page.locator("[data-cabinet-organization]").is_disabled(),
            {"context": company_context, "options": company_options},
        )
        company_page.wait_for_function(
            "() => { const node = document.querySelector('[data-cabinet-pill]'); return node && (node.textContent.includes('Готово') || node.textContent.includes('Пусто')); }",
            timeout=30000,
        )
        company_roster = _wait_for_t14_response(
            company_page,
            company_requests,
            "elms.cabinet.api.get_org_roster",
            company_roster_start,
        )
        company_mode = company_page.locator("[data-cabinet-mode]").text_content() or ""
        company_session = company_page.evaluate(
            "() => (window.frappe && window.frappe.session && window.frappe.session.user) || ''"
        )
        check(
            "company_admin_own_org_roster_continuity",
            bool(company_roster)
            and company_roster.get("http_status") == 200
            and company_roster.get("organization") == company_organization
            and "ограничен членством" in company_mode
            and company_session == os.environ.get("ELMS_BROWSER_TEST_USERNAME", ""),
            {
                "roster": company_roster,
                "mode": company_mode,
                "session": company_session,
            },
        )
        foreign_organization = next(
            (organization for organization in platform_organizations if organization != company_organization),
            "",
        )
        if foreign_organization:
            denial = declare_expected_denial(
                "company_admin_foreign_org_selection_denied",
                "company_admin",
                "elms.access.api.get_company_access_context",
            )
            foreign_start = len(company_requests)
            foreign_call = _call_t14(
                company_page,
                "elms.access.api.get_company_access_context",
                {"organization": foreign_organization},
            )
            foreign_entry = _wait_for_t14_response(
                company_page,
                company_requests,
                "elms.access.api.get_company_access_context",
                foreign_start,
            )
            denial.update(
                {
                    "observed": foreign_entry,
                    "call": foreign_call,
                    "status": "pass"
                    if foreign_entry and foreign_entry.get("http_status") == 403
                    else "fail",
                }
            )
            check(
                "company_admin_foreign_org_selection_denied",
                bool(foreign_entry) and foreign_entry.get("http_status") == 403,
                {"organization": foreign_organization, "response": foreign_entry, "call": foreign_call},
            )
        else:
            check("company_admin_foreign_org_selection_denied", False, "Platform directory has no foreign organization fixture")
        (
            journey["expected_console_errors"],
            journey["unexpected_console_errors"],
        ) = _classify_t14_console_errors(
            journey["console_errors"],
            journey["expected_denials"],
        )
        shared_request_failures = [
            failure
            for failure in journey["request_failures"]
            if _is_declared_a11_shared_request_failure(failure)
        ]
        task_request_failures = [
            failure
            for failure in journey["request_failures"]
            if not _is_declared_a11_shared_request_failure(failure)
        ]
        journey["non_blocking_shared_request_failures"] = shared_request_failures
        check(
            "t_a14_browser_runtime_errors_absent",
            not journey["unexpected_console_errors"] and not task_request_failures,
            {
                "expected_denials": journey["expected_denials"],
                "expected_console_errors": journey["expected_console_errors"],
                "unexpected_console_errors": journey["unexpected_console_errors"],
                "shared_request_failures": shared_request_failures,
                "request_failures": task_request_failures,
            },
        )
    except Exception as exc:
        journey["errors"].append(f"{type(exc).__name__}: {exc}")
    finally:
        if company_page is not None:
            if company_response_handler is not None:
                company_page.remove_listener("response", company_response_handler)
            company_page.remove_listener("console", on_console)
            company_page.remove_listener("requestfailed", on_request_failed)
        if platform_context is not None:
            platform_context.close()
        journey["api_requests"] = platform_requests + company_requests
        journey["status"] = "pass" if not journey["errors"] else "fail"
        results.setdefault("journeys", []).append(journey)
    if journey["status"] != "pass":
        results["passed"] = False
    return journey["status"] == "pass"


def _ensure_platform_owner_admission_flags() -> None:
    import subprocess

    sql = (
        "SET SQL_SAFE_UPDATES=0; "
        "UPDATE `tabELMS Organization` "
        "SET can_publish_own = 1, can_use_owner_catalog = 1 "
        f"WHERE name = '{B2B_WIRE_PLATFORM_OWNER}'"
    )
    commands = [
        [
            "bash",
            "scripts/docker-up.sh",
            "dev",
            "exec",
            "-T",
            "backend",
            "bench",
            "--site",
            "elms.localhost",
            "mariadb",
            "-e",
            sql,
        ],
        [
            "bash",
            "scripts/docker-up.sh",
            "dev",
            "exec",
            "-T",
            "backend",
            "bench",
            "--site",
            "elms.localhost",
            "clear-cache",
        ],
    ]
    for command in commands:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            detail = (completed.stderr or completed.stdout or "").strip()
            raise RuntimeError(
                "Failed to ensure platform-owner admission flags "
                f"(exit {completed.returncode}): {detail}"
            )


def _wire_course_setup(page) -> dict:
    return page.evaluate(
        """
        async ({courseCode, courseName, program, trainingKind, batchName, batchOrder, subscriptionContract, totalSeats}) => {
            const invoke = (method, args) => new Promise((resolve) => {
                let settled = false;
                const finish = (value) => {
                    if (!settled) {
                        settled = true;
                        resolve(value);
                    }
                };
                try {
                    frappe.call({
                        method,
                        args,
                        callback: (response) => finish({ok: true, message: response && response.message}),
                        error: (error) => finish({ok: false, error: (error && (error.message || error.exception)) || "request failed"}),
                    });
                } catch (error) {
                    finish({ok: false, error: (error && error.message) || "request failed"});
                }
            });
            const fail = (organization, error, details = {}) => ({ok: false, organization, error, ...details});
            const context = await invoke("elms.access.api.get_company_access_context", {});
            const organization = context.ok && context.message && String(context.message.organization || "").trim();
            if (!organization) {
                return fail("", context.error || "Company Admin organization is not resolved");
            }
            const organizationDocResult = await invoke("frappe.client.get", {
                doctype: "ELMS Organization",
                name: organization,
            });
            const organizationDoc = organizationDocResult.ok && organizationDocResult.message;
            if (!organizationDoc || organizationDoc.name !== organization) {
                return fail(organization, organizationDocResult.error || "Authenticated organization could not be read");
            }
            if (String(organizationDoc.status || "").trim() !== "Active") {
                return fail(organization, "Authenticated organization is not active", {organization_status: organizationDoc.status});
            }
            const organizationInn = String(organizationDoc.inn || "").trim();
            if (!organizationInn) {
                return fail(organization, "Authenticated organization has no persisted INN");
            }
            if (!Number(organizationDoc.can_publish_own || 0)) {
                return fail(
                    organization,
                    "Wire organization must have can_publish_own=1 before org-owned course admission",
                    {can_publish_own: organizationDoc.can_publish_own},
                );
            }

            const programListResult = await invoke("frappe.client.get_list", {
                doctype: "ELMS Program",
                filters: {organization, program_name: program},
                fields: ["name", "organization", "program_name"],
                order_by: "modified desc",
                limit_page_length: 20,
            });
            if (!programListResult.ok || !Array.isArray(programListResult.message)) {
                return fail(organization, programListResult.error || "Prepared program lookup failed");
            }
            if (programListResult.message.length > 1) {
                return fail(organization, "Prepared program name is ambiguous", {
                    program_candidates: programListResult.message.map((row) => row.name),
                });
            }
            let programDoc = programListResult.message.length === 1 ? programListResult.message[0] : null;
            if (!programDoc) {
                const createdProgram = await invoke("frappe.client.insert", {
                    doc: {
                        doctype: "ELMS Program",
                        organization,
                        program_name: program,
                        program_code: `${courseCode}-PROGRAM`,
                        total_hours: 16,
                        is_published: 1,
                        description: "Deterministic T-A12 B2B wire fixture program.",
                    },
                });
                if (!createdProgram.ok || !createdProgram.message) {
                    return fail(organization, createdProgram.error || "Prepared program creation failed");
                }
                programDoc = createdProgram.message;
            }
            if (
                !programDoc
                || programDoc.organization !== organization
                || programDoc.program_name !== program
            ) {
                return fail(organization, "Prepared program readback failed closed", {
                    program: programDoc && programDoc.name,
                    program_organization: programDoc && programDoc.organization,
                    program_name: programDoc && programDoc.program_name,
                });
            }
            const programValue = programDoc.name;

            const courseListResult = await invoke("frappe.client.get_list", {
                doctype: "ELMS Course",
                filters: {organization, course_code: courseCode},
                fields: ["name", "organization", "course_code"],
                order_by: "modified desc",
                limit_page_length: 20,
            });
            if (!courseListResult.ok || !Array.isArray(courseListResult.message)) {
                return fail(organization, courseListResult.error || "Prepared course lookup failed");
            }
            if (courseListResult.message.length > 1) {
                return fail(organization, "Prepared course code is ambiguous", {
                    course_candidates: courseListResult.message.map((row) => row.name),
                });
            }
            let courseId = courseListResult.message.length === 1 ? courseListResult.message[0].name : null;
            if (!courseId) {
                const createdCourse = await invoke("elms.lms.api.save_course", {
                    course_name: courseName,
                    course_code: courseCode,
                    academic_hours: 16,
                    is_published: 1,
                    passing_percentage: 80,
                    short_description: "Deterministic T-A12 B2B wire fixture course",
                    description: "Harness-owned course used only by the authenticated B2B wire lane.",
                });
                if (!createdCourse.ok || !createdCourse.message || !createdCourse.message.name) {
                    return fail(organization, createdCourse.error || "Prepared course creation failed");
                }
                courseId = createdCourse.message.name;
            }

            for (const [fieldname, value] of [["program", programValue], ["training_kind", trainingKind], ["status", "Active"]]) {
                const savedField = await invoke("frappe.client.set_value", {
                    doctype: "ELMS Course",
                    name: courseId,
                    fieldname,
                    value,
                });
                if (!savedField.ok) {
                    return fail(organization, savedField.error || `Prepared course ${fieldname} persistence failed`, {course: courseId});
                }
            }
            const courseResult = await invoke("frappe.client.get", {
                doctype: "ELMS Course",
                name: courseId,
            });
            const course = courseResult.ok && courseResult.message;
            const persistedProgram = String(course && course.program || "").trim();
            const persistedTrainingKind = String(course && course.training_kind || "").trim();
            const persistedCourseStatus = String(course && course.status || "").trim();
            const courseReady = Boolean(
                course
                && course.name === courseId
                && course.organization === organization
                && course.course_code === courseCode
                && persistedProgram === programValue
                && persistedTrainingKind === trainingKind
                && persistedCourseStatus === "Active"
            );
            if (!courseReady) {
                return fail(organization, courseResult.error || "Prepared course readback failed closed", {
                    course: courseId,
                    course_organization: course && course.organization,
                    course_code: course && course.course_code,
                    program: persistedProgram,
                    training_kind: persistedTrainingKind,
                    course_status: persistedCourseStatus,
                });
            }

            const listActiveBatches = async () => invoke("frappe.client.get_list", {
                doctype: "ELMS Batch",
                filters: {course: courseId, status: "Active"},
                fields: ["name", "organization", "course", "status", "batch_name"],
                order_by: "modified asc",
                limit_page_length: 20,
            });
            let activeBatchResult = await listActiveBatches();
            if (!activeBatchResult.ok || !Array.isArray(activeBatchResult.message)) {
                return fail(organization, activeBatchResult.error || "Prepared batch lookup failed", {course: courseId});
            }
            if (activeBatchResult.message.length > 1) {
                return fail(organization, "Prepared course has multiple active batches", {
                    course: courseId,
                    active_batch_count: activeBatchResult.message.length,
                    active_batch_candidates: activeBatchResult.message.map((row) => row.name),
                });
            }
            let batchId = activeBatchResult.message.length === 1 ? activeBatchResult.message[0].name : null;
            if (!batchId) {
                const createdBatch = await invoke("elms.lms.api.save_batch", {
                    batch_name: batchName,
                    course: courseId,
                    start_date: new Date().toISOString().slice(0, 10),
                    end_date: "2099-12-31",
                    organization,
                    order_number: batchOrder,
                    status: "Active",
                });
                if (!createdBatch.ok || !createdBatch.message || !createdBatch.message.name) {
                    return fail(organization, createdBatch.error || "Prepared active batch creation failed", {course: courseId});
                }
                batchId = createdBatch.message.name;
                activeBatchResult = await listActiveBatches();
            }
            if (!activeBatchResult.ok || !Array.isArray(activeBatchResult.message) || activeBatchResult.message.length !== 1) {
                return fail(organization, "Prepared course does not have exactly one active batch after setup", {
                    course: courseId,
                    active_batch_count: Array.isArray(activeBatchResult.message) ? activeBatchResult.message.length : null,
                    active_batch_candidates: Array.isArray(activeBatchResult.message) ? activeBatchResult.message.map((row) => row.name) : [],
                });
            }
            const batchResult = await invoke("frappe.client.get", {doctype: "ELMS Batch", name: batchId});
            const batch = batchResult.ok && batchResult.message;
            if (!batch || batch.name !== batchId || batch.organization !== organization || batch.course !== courseId || batch.status !== "Active") {
                return fail(organization, batchResult.error || "Prepared active batch ownership readback failed", {
                    course: courseId,
                    batch: batchId,
                    batch_organization: batch && batch.organization,
                    batch_course: batch && batch.course,
                    batch_status: batch && batch.status,
                });
            }

            const subscriptionListResult = await invoke("frappe.client.get_list", {
                doctype: "ELMS Subscription",
                filters: {organization, course: courseId},
                fields: ["name", "organization", "course", "contract_number", "total_seats", "seats_used", "status"],
                order_by: "modified asc",
                limit_page_length: 50,
            });
            if (!subscriptionListResult.ok || !Array.isArray(subscriptionListResult.message)) {
                return fail(organization, subscriptionListResult.error || "Prepared subscription lookup failed", {course: courseId});
            }
            const allSubscriptions = subscriptionListResult.message;
            const targetSubscription = allSubscriptions.find((row) => row.contract_number === subscriptionContract);
            const availableSubscriptions = allSubscriptions
                .filter((row) => row.status === "Active" && Number(row.total_seats) > Number(row.seats_used))
                .sort((left, right) => String(left.name).localeCompare(String(right.name)));
            let subscriptionId = availableSubscriptions.length ? availableSubscriptions[0].name : null;
            if (!subscriptionId && targetSubscription) {
                return fail(organization, "Deterministic wire subscription exists but has no available active seats", {
                    course: courseId,
                    subscription_id: targetSubscription.name,
                    subscription_status: targetSubscription.status,
                    total_seats: targetSubscription.total_seats,
                    seats_used: targetSubscription.seats_used,
                });
            }
            if (!subscriptionId) {
                const createdSubscription = await invoke("elms.lms.api.save_subscription", {
                    company_name: String(organizationDoc.organization_name || organization).trim(),
                    inn: organizationInn,
                    course: courseId,
                    organization,
                    contract_number: subscriptionContract,
                    total_seats: totalSeats,
                    valid_from: new Date().toISOString().slice(0, 10),
                    valid_to: "2099-12-31",
                    status: "Active",
                });
                if (!createdSubscription.ok || !createdSubscription.message || !createdSubscription.message.name) {
                    return fail(organization, createdSubscription.error || "Prepared active subscription creation failed", {course: courseId});
                }
                subscriptionId = createdSubscription.message.name;
            }
            const subscriptionResult = await invoke("frappe.client.get", {
                doctype: "ELMS Subscription",
                name: subscriptionId,
            });
            const subscription = subscriptionResult.ok && subscriptionResult.message;
            const subscriptionTotalSeats = Number(subscription && subscription.total_seats);
            const subscriptionSeatsUsed = Number(subscription && subscription.seats_used);
            const availableSeats = subscriptionTotalSeats - subscriptionSeatsUsed;
            const subscriptionReady = Boolean(
                subscription
                && subscription.name === subscriptionId
                && subscription.organization === organization
                && subscription.course === courseId
                && subscription.status === "Active"
                && Number.isFinite(availableSeats)
                && availableSeats > 0
            );
            if (!subscriptionReady) {
                return fail(organization, subscriptionResult.error || "Prepared subscription ownership/quota readback failed", {
                    course: courseId,
                    subscription_id: subscriptionId,
                    subscription_organization: subscription && subscription.organization,
                    subscription_course: subscription && subscription.course,
                    subscription_status: subscription && subscription.status,
                    total_seats: subscriptionTotalSeats,
                    seats_used: subscriptionSeatsUsed,
                    available_seats: availableSeats,
                });
            }
            return {
                ok: true,
                organization,
                organization_status: organizationDoc.status,
                course: courseId,
                course_organization: course.organization,
                course_code: course.course_code,
                course_status: persistedCourseStatus,
                program: persistedProgram,
                training_kind: persistedTrainingKind,
                batch: batchId,
                batch_organization: batch.organization,
                batch_course: batch.course,
                batch_status: batch.status,
                active_batch_count: 1,
                subscription_id: subscriptionId,
                subscription_organization: subscription.organization,
                subscription_course: subscription.course,
                subscription_status: subscription.status,
                total_seats: subscriptionTotalSeats,
                seats_used: subscriptionSeatsUsed,
                available_seats: availableSeats,
                selection_rule: "deterministic authenticated-organization course, exactly one active batch, and available active course-linked subscription",
            };
        }
        """,
        {
            "courseCode": B2B_WIRE_COURSE_CODE,
            "courseName": B2B_WIRE_COURSE_NAME,
            "program": B2B_WIRE_PROGRAM,
            "trainingKind": B2B_WIRE_TRAINING_KIND,
            "batchName": B2B_WIRE_BATCH_NAME,
            "batchOrder": B2B_WIRE_BATCH_ORDER,
            "subscriptionContract": B2B_WIRE_SUBSCRIPTION_CONTRACT,
            "totalSeats": B2B_WIRE_TOTAL_SEATS,
        },
    )


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


def _fixture_bytes(fixture: Path | dict[str, object]) -> bytes:
    if isinstance(fixture, Path):
        return fixture.read_bytes()
    content = fixture.get("buffer")
    if not isinstance(content, bytes):
        raise RuntimeError("Admission fixture buffer is unavailable")
    return content


def _admission_fixture_with_course_fields(
    valid_fixture: Path,
    *,
    program: str,
    training_kind: str,
) -> dict[str, object]:
    if not program or not training_kind:
        raise RuntimeError("Admission fixture requires non-empty course program and training kind")
    with ZipFile(BytesIO(_fixture_bytes(valid_fixture))) as source:
        entries = {name: source.read(name) for name in source.namelist()}
    sheet_name = "xl/worksheets/sheet1.xml"
    if sheet_name not in entries:
        raise RuntimeError("Valid admission fixture does not contain the first worksheet")

    namespace = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    root = ElementTree.fromstring(entries[sheet_name])
    first_data_row = None
    for row in root.iter(f"{{{namespace}}}row"):
        number_cell = next(
            (cell for cell in row if cell.attrib.get("r", "").startswith("B")),
            None,
        )
        value = next((node.text for node in number_cell or [] if node.tag.rsplit("}", 1)[-1] == "v"), None)
        if value == "1":
            first_data_row = row
            break
    if first_data_row is None:
        raise RuntimeError("Valid admission fixture does not contain a first data row")

    row_number = first_data_row.attrib.get("r")
    if not row_number:
        raise RuntimeError("Valid admission fixture first data row has no row number")
    for column, value in (("J", program), ("K", training_kind)):
        reference = f"{column}{row_number}"
        cell = next((item for item in first_data_row if item.attrib.get("r") == reference), None)
        if cell is None:
            cell = ElementTree.SubElement(first_data_row, f"{{{namespace}}}c", {"r": reference})
        cell.attrib["t"] = "inlineStr"
        for child in list(cell):
            cell.remove(child)
        inline = ElementTree.SubElement(cell, f"{{{namespace}}}is")
        text = ElementTree.SubElement(inline, f"{{{namespace}}}t")
        text.text = value
    entries[sheet_name] = ElementTree.tostring(root, encoding="utf-8", xml_declaration=True)

    workbook = BytesIO()
    with ZipFile(workbook, "w", compression=ZIP_DEFLATED) as target:
        for name, content in entries.items():
            target.writestr(name, content)
    return {
        "name": "admission-b2b-compatible.xlsx",
        "mimeType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "buffer": workbook.getvalue(),
    }


def _invalid_admission_fixture(valid_fixture: Path | dict[str, object]) -> dict[str, object]:
    """Return an in-memory copy of the valid workbook with one invalid row value."""

    with ZipFile(BytesIO(_fixture_bytes(valid_fixture))) as source:
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


def _run_admission_wire(
    page, base_url: str, results: dict
) -> tuple[bool, str | None, str | None, str | None]:
    admission_url = f"{base_url.rstrip('/')}/app/elms-admission"
    fixture_dir = ROOT / "memory-bank" / "app" / "clarify" / "fixtures-20261116-admission"
    source_fixture = fixture_dir / "sample-rpo-smetanin.xlsx"
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
    valid_import_id: str | None = None
    preferred_subscription_id: str | None = None
    preferred_course_id: str | None = None

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

        fixture_setup = _wire_course_setup(page)
        fixture_ready = bool(
            fixture_setup.get("ok")
            and fixture_setup.get("program")
            and fixture_setup.get("training_kind")
        )
        check("b2b_fixture_course_fields_present", fixture_ready, fixture_setup)
        if not fixture_ready:
            return False, None, None, None
        preferred_subscription_id = fixture_setup["subscription_id"]
        preferred_course_id = fixture_setup["course"]
        valid_fixture = _admission_fixture_with_course_fields(
            source_fixture,
            program=fixture_setup["program"],
            training_kind=fixture_setup["training_kind"],
        )
        invalid_fixture = _invalid_admission_fixture(valid_fixture)

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
        valid_import_id = valid_upload.get("name") if valid_upload else None
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
        return journey["status"] == "pass", valid_import_id, preferred_subscription_id, preferred_course_id
    except Exception as exc:
        journey["errors"].append(str(exc))
        return False, valid_import_id, preferred_subscription_id, preferred_course_id
    finally:
        results.setdefault("journeys", []).append(journey)


def _run_b2b_confirm_wire(
    page,
    base_url: str,
    import_id: str | None,
    preferred_subscription_id: str | None,
    preferred_course_id: str | None,
    results: dict,
) -> bool:
    """Exercise the authenticated T-A12 confirmation boundary through the cabinet UI."""

    learning_url = f"{base_url.rstrip('/')}/app/elms-learning"
    journey = {
        "journey_id": "JRN-T-A12-B2B-CONFIRM-001",
        "name": "Authenticated Company Admin confirms parsed import into quota-safe Active enrollments and sees result report",
        "url": learning_url,
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

    def check(name: str, passed: bool, observed) -> None:
        journey["checks"].append({"name": name, "status": "pass" if passed else "fail", "observed": observed})
        if not passed:
            journey["errors"].append(f"{name}: {observed}")

    page.on("response", lambda response: _record_admission_response(response, requests))
    page.on("console", on_console)
    page.on("requestfailed", on_request_failed)

    try:
        check("parsed_import_id_available", bool(import_id), import_id)
        if not import_id:
            return False

        page.goto(learning_url, timeout=30000, wait_until="networkidle")
        page.wait_for_selector(".elms-manager-tab:not([hidden])", state="visible", timeout=30000)
        page.locator(".elms-manager-tab").click()
        page.wait_for_selector("[data-admission-import]", state="visible", timeout=30000)
        check("company_admin_confirm_surface_loaded", True, page.url)

        subscription_setup = _attach_latest_active_subscription(
            page,
            import_id,
            preferred_subscription_id,
            preferred_course_id,
        )
        check("parsed_import_subscription_persisted", bool(subscription_setup.get("ok")), subscription_setup)
        if not subscription_setup.get("ok"):
            return False

        page.locator("[data-admission-import]").fill(import_id)
        page.evaluate(
            """() => {
                const preview = document.querySelector('[data-admission-preview]');
                if (preview) preview.textContent = '';
                const result = document.querySelector('[data-admission-result]');
                if (result) result.textContent = '';
            }"""
        )
        preview_before = len(requests)
        page.locator("[data-admission-preview-action]").click()
        page.wait_for_function(
            """() => {
                const node = document.querySelector('[data-admission-preview]');
                return node && node.textContent.includes('Осталось мест');
            }""",
            timeout=90000,
        )
        page.wait_for_timeout(250)
        preview_response = _api_request(requests[preview_before:], "preview_admission_import")
        preview_text = page.locator("[data-admission-preview]").text_content() or ""
        preview_remaining = preview_response.get("remaining_seats") if preview_response else None
        preview_selected = preview_response.get("selected_count") if preview_response else None
        preview_ok = bool(
            preview_response
            and preview_response.get("http_status") == 200
            and preview_response.get("status") == "preview"
            and isinstance(preview_selected, int)
            and preview_selected > 0
            and isinstance(preview_remaining, int)
            and preview_remaining >= preview_selected
            and "Осталось мест" in preview_text
        )
        check(
            "confirm_preview_exposes_remaining_quota",
            preview_ok,
            {
                "response": preview_response,
                "preview_text": preview_text,
            },
        )

        confirm_button = page.locator("[data-admission-confirm]")
        check("parsed_import_confirm_enabled", confirm_button.is_enabled(), confirm_button.is_enabled())
        confirm_before = len(requests)
        confirm_button.click()
        page.wait_for_function(
            """() => {
                const node = document.querySelector('[data-admission-result]');
                return node && node.textContent.trim().length > 0;
            }""",
            timeout=90000,
        )
        page.wait_for_timeout(250)
        confirm_response = _api_request(requests[confirm_before:], "confirm_admission_import")
        result_panel = page.locator("[data-admission-result]")
        result_text = result_panel.text_content() or ""
        enrolled_statuses = confirm_response.get("enrolled_statuses", []) if confirm_response else []
        enrolled_count = confirm_response.get("enrolled_count") if confirm_response else None
        remaining_seats = confirm_response.get("remaining_seats") if confirm_response else None
        selected_count = confirm_response.get("selected_count") if confirm_response else None
        quota_safe_active = bool(
            confirm_response
            and confirm_response.get("http_status") == 200
            and confirm_response.get("ok") is True
            and confirm_response.get("status") == "confirmed"
            and isinstance(selected_count, int)
            and selected_count > 0
            and isinstance(enrolled_count, int)
            and enrolled_count == selected_count
            and enrolled_count == len(enrolled_statuses)
            and enrolled_count > 0
            and all(status == "Active" for status in enrolled_statuses)
            and isinstance(preview_remaining, int)
            and isinstance(remaining_seats, int)
            and remaining_seats == preview_remaining - enrolled_count
            and remaining_seats >= 0
        )
        check(
            "confirmed_rows_are_quota_safe_active_enrollments",
            quota_safe_active,
            {
                "response": confirm_response,
                "enrolled_statuses": enrolled_statuses,
                "preview_remaining_seats": preview_remaining,
            },
        )

        success_report = "Зачислено:" in result_text and "Осталось мест:" in result_text
        error_report = result_panel.locator(".text-danger").count() > 0
        check(
            "confirm_result_report_is_explicit",
            success_report or error_report,
            {
                "success_report": success_report,
                "error_report": error_report,
                "result_text": result_text,
            },
        )
        check(
            "browser_runtime_errors_absent",
            not journey["console_errors"] and not journey["request_failures"],
            {"console_errors": journey["console_errors"], "request_failures": journey["request_failures"]},
        )
        journey["status"] = "pass" if not journey["errors"] else "fail"
        return journey["status"] == "pass"
    except Exception as exc:
        journey["errors"].append(str(exc))
        return False
    finally:
        results.setdefault("journeys", []).append(journey)


def _record_custom_fields_response(response, requests: list[dict]) -> None:
    method = _method_name(response.url)
    tracked_methods = {
        "elms.access.api.get_company_access_context",
        "elms.lms.api.custom_fields.get_custom_field_schema",
        "elms.lms.api.custom_fields.save_custom_field_definition",
        "elms.lms.api.custom_fields.get_custom_field_form_data",
        "frappe.client.get",
        "frappe.client.get_list",
        "frappe.desk.form.save.savedocs",
    }
    if method not in tracked_methods:
        return
    entry = {"method": method, "status": response.status, "http_status": response.status}
    try:
        payload = response.json()
        message = payload.get("message") if isinstance(payload, dict) else None
        if method.endswith("get_company_access_context") and isinstance(message, dict):
            entry["organization"] = message.get("organization")
        elif method.endswith("get_custom_field_schema") and isinstance(message, dict):
            definitions = message.get("definitions")
            entry["target_doctype"] = message.get("target_doctype")
            entry["definition_count"] = len(definitions) if isinstance(definitions, list) else None
            entry["field_keys"] = [
                definition.get("field_key")
                for definition in definitions
                if isinstance(definition, dict)
            ] if isinstance(definitions, list) else []
        elif method.endswith("save_custom_field_definition") and isinstance(message, dict):
            definition = message.get("definition")
            if isinstance(definition, dict):
                entry["definition"] = {
                    key: definition.get(key)
                    for key in ("name", "organization", "applies_to", "field_key", "label", "field_type", "schema_version")
                }
        elif method.endswith("get_custom_field_form_data") and isinstance(message, dict):
            entry["target_doctype"] = message.get("target_doctype")
            entry["target_name"] = message.get("target_name")
            entry["stored_values"] = message.get("stored_values")
        elif method == "frappe.desk.form.save.savedocs" and isinstance(message, dict):
            entry["doctype"] = message.get("doctype")
            entry["name"] = message.get("name")
            entry["custom_field_values"] = message.get("custom_field_values")
        elif method == "frappe.client.get" and isinstance(message, dict):
            entry["doctype"] = message.get("doctype")
            entry["name"] = message.get("name")
            entry["custom_field_values"] = message.get("custom_field_values")
    except Exception:
        entry["json"] = False
    requests.append(entry)


def _run_t_a13_custom_fields_wire(
    page,
    base_url: str,
    preferred_course_id: str | None,
    results: dict,
) -> bool:
    """Exercise the authenticated T-A13 definition and Course-value wire boundary."""

    custom_fields_url = f"{base_url.rstrip('/')}/app/elms-custom-fields"
    journey = {
        "journey_id": "JRN-T-A13-CUSTOM-FIELDS-001",
        "name": "Authenticated Company Admin defines a Course field and saves/readbacks its Additional value",
        "url": custom_fields_url,
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

    def check(name: str, passed: bool, observed) -> None:
        journey["checks"].append({"name": name, "status": "pass" if passed else "fail", "observed": observed})
        if not passed:
            journey["errors"].append(f"{name}: {observed}")

    def api_call(method: str, args: dict) -> dict:
        return page.evaluate(
            """
            async ({method, args}) => new Promise((resolve) => {
                let settled = false;
                const finish = (value) => {
                    if (!settled) {
                        settled = true;
                        resolve(value);
                    }
                };
                try {
                    frappe.call({
                        method,
                        args,
                        callback: (response) => finish({ok: true, message: response && response.message}),
                        error: (error) => finish({ok: false, error: (error && (error.message || error.exception)) || "request failed"}),
                    });
                } catch (error) {
                    finish({ok: false, error: (error && error.message) || "request failed"});
                }
            })
            """,
            {"method": method, "args": args},
        )

    page.on("response", lambda response: _record_custom_fields_response(response, requests))
    page.on("console", on_console)
    page.on("requestfailed", on_request_failed)

    try:
        context = api_call("elms.access.api.get_company_access_context", {})
        organization = str((context.get("message") or {}).get("organization") or "").strip() if context.get("ok") else ""
        check(
            "custom_fields_authenticated_organization_resolved",
            bool(organization),
            {"ok": context.get("ok"), "organization": organization, "error": context.get("error")},
        )
        if not organization:
            return False

        course_id = preferred_course_id
        if course_id:
            course_result = api_call("frappe.client.get", {"doctype": "ELMS Course", "name": course_id})
        else:
            course_result = api_call(
                "frappe.client.get_list",
                {
                    "doctype": "ELMS Course",
                    "filters": {"organization": organization, "status": "Active"},
                    "fields": ["name", "organization", "course_code", "status"],
                    "order_by": "modified desc",
                    "limit_page_length": 20,
                },
            )
        course_message = course_result.get("message") if course_result.get("ok") else None
        course = course_message if isinstance(course_message, dict) else (
            course_message[0] if isinstance(course_message, list) and course_message else None
        )
        course_id = str((course or {}).get("name") or "").strip()
        course_ready = bool(course_id and course and course.get("organization") == organization)
        check(
            "custom_fields_course_owned_by_authenticated_organization",
            course_ready,
            {
                "course": course_id,
                "organization": organization,
                "course_organization": (course or {}).get("organization"),
                "course_code": (course or {}).get("course_code"),
                "status": (course or {}).get("status"),
            },
        )
        if not course_ready:
            return False

        existing_schema = api_call(
            "elms.lms.api.custom_fields.get_custom_field_schema",
            {"target_doctype": "ELMS Course", "organization": organization},
        )
        existing_definitions = (existing_schema.get("message") or {}).get("definitions", []) if existing_schema.get("ok") else []
        existing = next(
            (
                definition for definition in existing_definitions
                if isinstance(definition, dict) and definition.get("field_key") == T_A13_CUSTOM_FIELD_KEY
            ),
            None,
        )
        if existing and existing.get("name"):
            cleanup = api_call(
                "elms.lms.api.custom_fields.delete_custom_field_definition",
                {"name": existing["name"], "organization": organization},
            )
            check(
                "custom_fields_previous_fixture_removed",
                bool(cleanup.get("ok")),
                {"definition": existing, "cleanup": cleanup},
            )
            if not cleanup.get("ok"):
                return False

        page.goto(custom_fields_url, timeout=30000, wait_until="domcontentloaded")
        page.wait_for_selector(".elms-custom-fields-page", state="visible", timeout=30000)
        page.wait_for_function(
            """() => {
                const select = document.querySelector('.elms-custom-fields-toolbar select');
                return select && select.value;
            }""",
            timeout=30000,
        )
        check("custom_fields_definition_surface_loaded", True, page.url)

        toolbar_selects = page.locator(".elms-custom-fields-toolbar select")
        target_select = toolbar_selects.nth(1)
        target_select.select_option("ELMS Course")
        definition_inputs = page.locator(".elms-custom-fields-definition-form input[type='text']")
        definition_inputs.nth(0).fill(T_A13_CUSTOM_FIELD_KEY)
        definition_inputs.nth(1).fill(T_A13_CUSTOM_FIELD_LABEL)
        page.locator(".elms-custom-fields-definition-form select").select_option("text")
        save_definition = page.locator(".elms-custom-fields-save")
        with page.expect_response(
            lambda response: _is_post_response(
                response,
                "elms.lms.api.custom_fields.save_custom_field_definition",
            ),
            timeout=30000,
        ) as definition_response_info:
            save_definition.click()
        definition_response = definition_response_info.value
        check(
            "custom_field_definition_api_succeeded",
            definition_response.status == 200,
            {"http_status": definition_response.status},
        )
        if definition_response.status != 200:
            return False
        page.wait_for_function(
            """(fieldKey) => Array.from(document.querySelectorAll('.elms-custom-fields-list-item'))
                .some((item) => item.textContent.includes(fieldKey))""",
            arg=T_A13_CUSTOM_FIELD_KEY,
            timeout=30000,
        )
        definition_schema = api_call(
            "elms.lms.api.custom_fields.get_custom_field_schema",
            {"target_doctype": "ELMS Course", "organization": organization},
        )
        definition_data = (definition_schema.get("message") or {}).get("definitions", []) if definition_schema.get("ok") else []
        persisted_definition = next(
            (
                definition for definition in definition_data
                if isinstance(definition, dict) and definition.get("field_key") == T_A13_CUSTOM_FIELD_KEY
            ),
            None,
        )
        definition_saved = bool(
            definition_response.status == 200
            and persisted_definition
            and persisted_definition.get("organization") == organization
            and persisted_definition.get("applies_to") == "ELMS Course"
            and persisted_definition.get("field_type") == "text"
        )
        check(
            "custom_field_definition_saved_and_read_back",
            definition_saved,
            {
                "http_status": definition_response.status,
                "definition": persisted_definition,
                "ui_list_contains_key": page.locator(".elms-custom-fields-list-item").all_text_contents(),
            },
        )
        if not definition_saved:
            return False

        course_url = f"{base_url.rstrip('/')}/app/elms-course/{quote(course_id, safe='')}"
        page.goto(course_url, timeout=30000, wait_until="domcontentloaded")
        page.wait_for_selector(".form-page", state="visible", timeout=30000)
        page.wait_for_selector(
            f".elms-custom-field-control[data-field-key='{T_A13_CUSTOM_FIELD_KEY}']",
            state="visible",
            timeout=30000,
        )
        course_control = page.locator(f".elms-custom-field-control[data-field-key='{T_A13_CUSTOM_FIELD_KEY}']")
        check("course_additional_field_control_rendered", course_control.count() == 1, page.url)
        course_control.fill(T_A13_CUSTOM_FIELD_VALUE)
        course_control.dispatch_event("change")
        course_control.fill("")
        course_control.dispatch_event("change")
        course_control.fill(T_A13_CUSTOM_FIELD_VALUE)
        course_control.dispatch_event("change")
        page.wait_for_function(
            """(fieldKey, expected) => {
                const raw = window.cur_frm && window.cur_frm.doc && window.cur_frm.doc.custom_field_values;
                let values = raw;
                if (typeof raw === 'string') {
                    try { values = JSON.parse(raw); } catch (error) { return false; }
                }
                return values && values[fieldKey] === expected;
            }""",
            arg=(T_A13_CUSTOM_FIELD_KEY, T_A13_CUSTOM_FIELD_VALUE),
            timeout=30000,
        )
        save_course = page.locator("button.primary-action").first
        with page.expect_response(
            lambda response: _is_post_response(response, "frappe.desk.form.save.savedocs"),
            timeout=30000,
        ) as course_save_response_info:
            save_course.click()
        course_save_response = course_save_response_info.value
        page.wait_for_function(
            """() => window.cur_frm && !window.cur_frm.is_dirty()""",
            timeout=30000,
        )
        form_readback = api_call(
            "elms.lms.api.custom_fields.get_custom_field_form_data",
            {
                "target_doctype": "ELMS Course",
                "target_name": course_id,
                "organization": organization,
            },
        )
        raw_readback = api_call("frappe.client.get", {"doctype": "ELMS Course", "name": course_id})
        form_data = form_readback.get("message") if form_readback.get("ok") else None
        raw_course = raw_readback.get("message") if raw_readback.get("ok") else None
        stored_values = (form_data or {}).get("stored_values") if isinstance(form_data, dict) else None
        raw_values = (raw_course or {}).get("custom_field_values") if isinstance(raw_course, dict) else None
        if isinstance(raw_values, str):
            try:
                raw_values = json.loads(raw_values)
            except (TypeError, ValueError):
                raw_values = None
        value_saved = bool(
            course_save_response.status == 200
            and isinstance(stored_values, dict)
            and stored_values.get(T_A13_CUSTOM_FIELD_KEY) == T_A13_CUSTOM_FIELD_VALUE
            and isinstance(raw_values, dict)
            and raw_values.get(T_A13_CUSTOM_FIELD_KEY) == T_A13_CUSTOM_FIELD_VALUE
        )
        check(
            "course_additional_value_saved_and_read_back",
            value_saved,
            {
                "save_http_status": course_save_response.status,
                "form_api_readback": stored_values,
                "course_document_readback": raw_values,
                "course": course_id,
                "organization": organization,
            },
        )
        check(
            "browser_runtime_errors_absent",
            not journey["console_errors"] and not journey["request_failures"],
            {"console_errors": journey["console_errors"], "request_failures": journey["request_failures"]},
        )
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
    _set_ac_disposition(results)
    results["task_scope"] = {
        "task_id": "T-A14-elms-admin-org-view-all",
        "required_journeys": ["JRN-T-A14-ADMIN-ORG-VIEW-001"],
        "non_blocking_shared_journeys": [
            T_A11_SHARED_JOURNEY_ID,
            "JRN-T-A13-CUSTOM-FIELDS-001",
        ],
        "declared_non_blocking_failures": [
            {
                "journey_id": T_A11_SHARED_JOURNEY_ID,
                "method": T_A11_SHARED_REQUEST_FAILURE_METHOD,
                "failure": T_A11_SHARED_REQUEST_FAILURE,
                "reason": "Independent A11 admission coverage is retained as evidence and does not gate T-A14.",
            }
        ],
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

    if not smoke_only and runtime_ready:
        try:
            _ensure_platform_owner_admission_flags()
        except Exception as exc:
            results["passed"] = False
            results["errors"].append(str(exc))

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
            response = _navigate_to_login(page, login_url)
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
            login_heading = page.locator(LOGIN_READY_SELECTOR).first
            login_heading.wait_for(state="visible", timeout=15000)
            heading = login_heading.text_content(timeout=5000) or ""
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
                _navigate_to_login(page, login_url)
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
                    if not _run_t_a14_wire(page, browser, base_url, results):
                        results["passed"] = False
                    custom_course_id = None
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
                        a11_passed, import_id, subscription_id, course_id = _run_admission_wire(page, base_url, results)
                        custom_course_id = course_id
                        if not a11_passed:
                            results.setdefault("non_blocking_shared_journey_failures", []).append(
                                {
                                    "journey_id": T_A11_SHARED_JOURNEY_ID,
                                    "disposition": "out_of_scope_non_blocking",
                                    "reason": "T-A11 admission coverage is retained as evidence; only the declared T-A14 journey gates this task result.",
                                    "declared_failures": [
                                        {
                                            "method": T_A11_SHARED_REQUEST_FAILURE_METHOD,
                                            "failure": T_A11_SHARED_REQUEST_FAILURE,
                                        }
                                    ],
                                }
                            )
                        if not _run_b2b_confirm_wire(
                            page,
                            base_url,
                            import_id,
                            subscription_id,
                            course_id,
                            results,
                        ):
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
                    t_a13_passed = _run_t_a13_custom_fields_wire(page, base_url, custom_course_id, results)
                    if not t_a13_passed:
                        results.setdefault("non_blocking_shared_journey_failures", []).append(
                            {
                                "journey_id": "JRN-T-A13-CUSTOM-FIELDS-001",
                                "disposition": "out_of_scope_non_blocking",
                                "reason": "T-A14 VERIFY is gated by its authenticated organization-view journey; unrelated T-A13 failures are retained as evidence only.",
                            }
                        )
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

        except LoginReadinessError as exc:
            message = str(exc)
            results["passed"] = False
            results["checks"].append(
                {
                    "name": "login_page_readiness",
                    "status": "fail",
                    "observed": message,
                }
            )
            results["errors"].append(message)
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
