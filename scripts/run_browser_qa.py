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

            # 3. Check CSS link in DOM
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

            # 4. Check Keycloak button
            btn = page.query_selector(".btn-keycloak")
            has_btn = btn is not None
            check_btn = {
                "name": "btn_keycloak_present",
                "status": "pass" if has_btn else "fail",
            }
            results["checks"].append(check_btn)
            if not has_btn:
                results["passed"] = False
                results["errors"].append(".btn-keycloak button not found on login page")

            # 5. Check no Yandex button
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

            if btn:
                # 6. Check href
                href = btn.get_attribute("href") or ""
                valid_prefix = "http://127.0.0.1:8480/realms/elms/protocol/openid-connect/auth"
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
                    results["errors"].append(f"Button href contains internal hostname keycloak:8080")

                # 7. Check computed styles (AC-002)
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

            # Screenshot
            screenshot_path = ARTIFACTS_DIR / "login-page.png"
            page.screenshot(path=str(screenshot_path))
            results["screenshot"] = str(screenshot_path)

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
