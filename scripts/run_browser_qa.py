#!/usr/bin/env python3
"""Run automated browser QA tests for ELMS Keycloak Login UI via Playwright."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
ARTIFACTS_DIR = ROOT / "browser-artifacts"


def run_browser_checks(base_url: str, smoke_only: bool = False) -> dict:
    from playwright.sync_api import sync_playwright

    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
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

    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=executable_path if Path(executable_path).exists() else None,
            headless=True,
        )
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()
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
            check_branding = {
                "name": "login_heading_uses_elms_sdo_brand",
                "status": "pass" if "ELMS СДО" in heading else "fail",
                "observed": heading.strip(),
            }
            results["checks"].append(check_branding)
            if "ELMS СДО" not in heading:
                results["passed"] = False
                results["errors"].append(
                    f"Login heading is '{heading.strip()}', expected it to contain 'ELMS СДО'"
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
                "email_link": {"height": "44px", "borderRadius": "3px"},
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

            # 7. Check Keycloak button (exactly one)
            keycloak_buttons = page.query_selector_all(".btn-keycloak")
            has_single_btn = len(keycloak_buttons) == 1
            check_btn = {
                "name": "btn_keycloak_present",
                "status": "pass" if has_single_btn else "fail",
            }
            results["checks"].append(check_btn)
            if not has_single_btn:
                results["passed"] = False
                results["errors"].append(
                    f"Expected exactly one .btn-keycloak button, found {len(keycloak_buttons)}"
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

            if keycloak_buttons:
                btn = keycloak_buttons[0]
                href = btn.get_attribute("href") or ""
                valid_prefix = "http://127.0.0.1:8480/realms/elms"
                no_container_host = "keycloak:8080" not in href
                starts_correctly = href.startswith(valid_prefix)
                check_href = {
                    "name": "btn_keycloak_href_public_url",
                    "status": "pass" if (starts_correctly and no_container_host) else "fail",
                    "href": href,
                }
                results["checks"].append(check_href)
                if not starts_correctly:
                    results["passed"] = False
                    results["errors"].append(f"Button href '{href}' does not start with '{valid_prefix}'")
                if not no_container_host:
                    results["passed"] = False
                    results["errors"].append("Button href contains internal hostname keycloak:8080")

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
                    btn,
                )
                results["computed_style"] = computed

                # Geometry: height 44px, radius 3px
                height_ok = computed.get("height") == "44px"
                radius_ok = computed.get("borderRadius") == "3px"
                # Color: cobalt #0d4cd3 = rgb(13, 76, 211)
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

            screenshot_path = ARTIFACTS_DIR / "login-page.png"
            page.screenshot(path=str(screenshot_path))
            results["screenshot"] = str(screenshot_path)

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
                login_form = page.locator(".for-login form.form-login").first
                login_form.locator("#login_email").fill(test_username)
                login_form.locator("#login_password").fill(test_password)
                login_form.locator(".btn-login").click()
                try:
                    page.wait_for_url("**/app**", timeout=15000)
                    success = True
                except Exception:
                    success = False
                check_success = {
                    "name": "valid_keycloak_credentials_reach_app",
                    "status": "pass" if success else "fail",
                    "observed": page.url,
                }
                results["checks"].append(check_success)
                if not success:
                    results["passed"] = False
                    results["errors"].append(
                        f"Valid Keycloak credentials did not reach /app (current URL: {page.url})"
                    )

        finally:
            browser.close()

    evidence_file = ARTIFACTS_DIR / "browser-evidence.json"
    results.update(
        {
            "status": "pass" if results["passed"] else "fail",
            "evidence_type": "runtime_browser",
            "live_evidence": True,
            "timestamp": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "command": "python3 scripts/run_browser_qa.py",
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
