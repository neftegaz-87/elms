"""Site configuration injection helper for ELMS Single Sign-On."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Mapping

from elms.sso.constants import (
    DEFAULT_SSO_ROLES,
    DEFAULT_SSO_ROLES_CONF_KEY,
    KEYCLOAK_LOGIN_CONF_KEY,
)
from elms.sso.settings import SsoSettings, parse_roles_list

_LEGACY_DIRECT_IDP_KEY = "_".join(["yandex", "login"])


def parse_roles(raw_roles: str | list[str] | tuple[str, ...] | None) -> list[str]:
    """Parse comma-separated or list of role names into a clean list of strings."""
    return parse_roles_list(raw_roles)


def build_sso_site_config(env: Mapping[str, str] | None = None) -> dict[str, object]:
    """Build SSO configuration dictionary from environment variables.

    Never generates a direct external IdP login dictionary for Frappe.
    """
    settings = SsoSettings.from_env(env)
    return settings.to_site_config()


def inject_sso_site_config(
    site_config_path: str | Path | None = None,
    site_name: str | None = None,
    env: Mapping[str, str] | None = None,
) -> dict[str, object]:
    """Inject SSO configuration into site_config.json.

    Returns the updated site_config dictionary.
    """
    target_path: Path
    if site_config_path is not None:
        target_path = Path(site_config_path)
    else:
        try:
            import frappe
            if getattr(frappe, "local", None) and getattr(frappe.local, "site", None):
                target_path = Path(frappe.get_site_path("site_config.json"))
            else:
                name = site_name or os.environ.get("SITE_NAME") or "elms.localhost"
                sites_dir = Path(os.environ.get("SITES_DIR") or "sites")
                target_path = sites_dir / name / "site_config.json"
        except Exception:
            name = site_name or os.environ.get("SITE_NAME") or "elms.localhost"
            sites_dir = Path(os.environ.get("SITES_DIR") or "sites")
            target_path = sites_dir / name / "site_config.json"

    sso_cfg = build_sso_site_config(env=env)

    site_data: dict[str, object] = {}
    if target_path.exists():
        try:
            with open(target_path, "r", encoding="utf-8") as f:
                site_data = json.load(f)
        except (json.JSONDecodeError, OSError):
            site_data = {}

    # Update or clear keycloak_login
    if KEYCLOAK_LOGIN_CONF_KEY in sso_cfg:
        site_data[KEYCLOAK_LOGIN_CONF_KEY] = sso_cfg[KEYCLOAK_LOGIN_CONF_KEY]
    else:
        site_data.pop(KEYCLOAK_LOGIN_CONF_KEY, None)

    # Set default roles
    site_data[DEFAULT_SSO_ROLES_CONF_KEY] = sso_cfg[DEFAULT_SSO_ROLES_CONF_KEY]

    # Ensure forbidden direct IdP key is never present
    site_data.pop(_LEGACY_DIRECT_IDP_KEY, None)

    target_path.parent.mkdir(parents=True, exist_ok=True)
    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(site_data, f, indent=1, ensure_ascii=False)
        f.write("\n")

    return site_data


if __name__ == "__main__":
    inject_sso_site_config()
