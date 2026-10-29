"""Typed environment settings adapter for ELMS Single Sign-On."""

from __future__ import annotations

import json
from typing import Any, Mapping
from urllib.parse import urlparse

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from elms.sso.constants import (
    DEFAULT_SSO_ROLES,
    DEFAULT_SSO_ROLES_CONF_KEY,
    ENV_ELMS_SSO_DEFAULT_ROLES,
    ENV_ELMS_SSO_REQUIRE,
    ENV_KEYCLOAK_CLIENT_ID,
    ENV_KEYCLOAK_CLIENT_SECRET,
    ENV_KEYCLOAK_PUBLIC_URL,
    ENV_YANDEX_CLIENT_ID,
    ENV_YANDEX_CLIENT_SECRET,
    KEYCLOAK_LOGIN_CONF_KEY,
)


def parse_roles_list(raw_roles: Any) -> list[str]:
    """Parse raw role representation into clean list of strings."""
    if not raw_roles:
        return list(DEFAULT_SSO_ROLES)
    if isinstance(raw_roles, (list, tuple)):
        return [str(r).strip() for r in raw_roles if str(r).strip()]
    if isinstance(raw_roles, str):
        stripped = raw_roles.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            try:
                parsed = json.loads(stripped)
                if isinstance(parsed, list):
                    return [str(r).strip() for r in parsed if str(r).strip()]
            except (json.JSONDecodeError, ValueError):
                pass
        return [r.strip() for r in stripped.split(",") if r.strip()]
    return list(DEFAULT_SSO_ROLES)


class SsoSettings(BaseSettings):
    """Typed SSO environment settings with fail-closed validation.

    Covers all contract environment variables:
    - KEYCLOAK_CLIENT_ID
    - KEYCLOAK_CLIENT_SECRET
    - KEYCLOAK_PUBLIC_URL
    - YANDEX_CLIENT_ID
    - YANDEX_CLIENT_SECRET
    - ELMS_SSO_DEFAULT_ROLES
    - ELMS_SSO_REQUIRE
    """

    model_config = SettingsConfigDict(
        case_sensitive=False,
        populate_by_name=True,
        extra="ignore",
    )

    keycloak_client_id: str | None = Field(default=None, alias=ENV_KEYCLOAK_CLIENT_ID)
    keycloak_client_secret: SecretStr | None = Field(
        default=None, alias=ENV_KEYCLOAK_CLIENT_SECRET
    )
    keycloak_public_url: str | None = Field(default=None, alias=ENV_KEYCLOAK_PUBLIC_URL)
    yandex_client_id: str | None = Field(default=None, alias=ENV_YANDEX_CLIENT_ID)
    yandex_client_secret: SecretStr | None = Field(
        default=None, alias=ENV_YANDEX_CLIENT_SECRET
    )
    elms_sso_default_roles: list[str] | str = Field(
        default_factory=lambda: list(DEFAULT_SSO_ROLES),
        alias=ENV_ELMS_SSO_DEFAULT_ROLES,
    )
    elms_sso_require: bool | str = Field(default=False, alias=ENV_ELMS_SSO_REQUIRE)

    @field_validator("keycloak_client_id", "yandex_client_id", mode="before")
    @classmethod
    def _validate_str(cls, value: Any) -> str | None:
        if value is None:
            return None
        cleaned = str(value).strip()
        return cleaned if cleaned else None

    @field_validator("keycloak_client_secret", "yandex_client_secret", mode="before")
    @classmethod
    def _validate_secret(cls, value: Any) -> SecretStr | None:
        if value is None:
            return None
        if isinstance(value, SecretStr):
            return value if value.get_secret_value().strip() else None
        cleaned = str(value).strip()
        return SecretStr(cleaned) if cleaned else None

    @field_validator("keycloak_public_url", mode="before")
    @classmethod
    def _validate_public_url(cls, value: Any) -> str | None:
        if value is None:
            return None
        cleaned = str(value).strip().rstrip("/")
        if not cleaned:
            return None
        parsed = urlparse(cleaned)
        if "keycloak:8080" in cleaned or parsed.netloc == "keycloak:8080" or parsed.hostname == "keycloak":
            raise ValueError(
                f"KEYCLOAK_PUBLIC_URL cannot use container internal hostname keycloak:8080: {cleaned}"
            )
        if not (parsed.scheme in ("http", "https") and parsed.netloc):
            raise ValueError(
                f"KEYCLOAK_PUBLIC_URL must be a valid http or https absolute URL: {cleaned}"
            )
        return cleaned

    @field_validator("elms_sso_default_roles", mode="after")
    @classmethod
    def _validate_roles(cls, value: Any) -> list[str]:
        return parse_roles_list(value)

    @field_validator("elms_sso_require", mode="after")
    @classmethod
    def _validate_require(cls, value: Any) -> bool:
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in {"1", "true", "yes", "on"}

    @model_validator(mode="after")
    def _validate_fail_closed(self) -> SsoSettings:
        if self.elms_sso_require:
            if not self.keycloak_client_id or not self.keycloak_client_secret:
                raise ValueError(
                    "ELMS_SSO_REQUIRE is enabled but KEYCLOAK_CLIENT_ID or KEYCLOAK_CLIENT_SECRET is missing."
                )
        return self

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> SsoSettings:
        """Create SsoSettings instance from explicit mapping or environment variables."""
        if env is None:
            return cls()
        explicit_roles = env.get(ENV_ELMS_SSO_DEFAULT_ROLES)
        if explicit_roles is None:
            explicit_roles = env.get("elms_sso_default_roles")
        if explicit_roles is None:
            roles_val = list(DEFAULT_SSO_ROLES)
        else:
            roles_val = explicit_roles

        return cls(
            keycloak_client_id=env.get(ENV_KEYCLOAK_CLIENT_ID) or env.get("keycloak_client_id"),
            keycloak_client_secret=env.get(ENV_KEYCLOAK_CLIENT_SECRET) or env.get("keycloak_client_secret"),
            keycloak_public_url=env.get(ENV_KEYCLOAK_PUBLIC_URL) or env.get("keycloak_public_url"),
            yandex_client_id=env.get(ENV_YANDEX_CLIENT_ID) or env.get("yandex_client_id"),
            yandex_client_secret=env.get(ENV_YANDEX_CLIENT_SECRET) or env.get("yandex_client_secret"),
            elms_sso_default_roles=roles_val,
            elms_sso_require=env.get(ENV_ELMS_SSO_REQUIRE) or env.get("elms_sso_require") or False,
        )

    def to_site_config(self) -> dict[str, object]:
        """Produce Frappe site_config SSO fragment.

        Never produces direct external IdP login keys (e.g. legacy direct IdP).
        """
        config: dict[str, object] = {}
        if self.keycloak_client_id and self.keycloak_client_secret:
            config[KEYCLOAK_LOGIN_CONF_KEY] = {
                "client_id": self.keycloak_client_id,
                "client_secret": self.keycloak_client_secret.get_secret_value(),
            }
        config[DEFAULT_SSO_ROLES_CONF_KEY] = list(self.elms_sso_default_roles)
        return config
