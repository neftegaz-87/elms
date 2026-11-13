"""Typed, server-only Keycloak Admin API client for ELMS invitations."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Mapping
from urllib.parse import quote

import requests


class KeycloakProvisionError(RuntimeError):
    """Base error for a failed Keycloak provisioning boundary."""


class KeycloakConfigError(KeycloakProvisionError):
    """Required server-side Keycloak Admin configuration is absent or invalid."""


class KeycloakAuthError(KeycloakProvisionError):
    """Keycloak rejected the Admin API credentials."""


class KeycloakTransportError(KeycloakProvisionError):
    """Network or timeout failure while calling Keycloak."""


@dataclass(frozen=True, slots=True)
class KeycloakAdminSettings:
    base_url: str
    realm: str
    client_id: str
    client_secret: str
    timeout_seconds: float = 8.0

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> "KeycloakAdminSettings":
        values = os.environ if environ is None else environ
        base_url = str(values.get("KEYCLOAK_ADMIN_BASE_URL") or values.get("KEYCLOAK_INTERNAL_URL") or "").strip().rstrip("/")
        realm = str(values.get("KEYCLOAK_ADMIN_REALM") or "elms").strip()
        client_id = str(values.get("KEYCLOAK_ADMIN_CLIENT_ID") or "").strip()
        client_secret = str(values.get("KEYCLOAK_ADMIN_CLIENT_SECRET") or "").strip()
        if not base_url.startswith(("http://", "https://")) or not realm or not client_id or not client_secret:
            raise KeycloakConfigError("Keycloak Admin API configuration is incomplete")
        try:
            timeout = float(values.get("KEYCLOAK_ADMIN_TIMEOUT_SECONDS") or 8)
        except (TypeError, ValueError) as error:
            raise KeycloakConfigError("KEYCLOAK_ADMIN_TIMEOUT_SECONDS is invalid") from error
        if timeout <= 0 or timeout > 60:
            raise KeycloakConfigError("KEYCLOAK_ADMIN_TIMEOUT_SECONDS must be between 0 and 60")
        return cls(base_url, realm, client_id, client_secret, timeout)


class KeycloakAdminClient:
    """Small OpenID Connect Admin API client with typed fail-closed errors."""

    def __init__(self, settings: KeycloakAdminSettings, session: Any | None = None):
        self.settings = settings
        self.session = session or requests.Session()
        self._token: str | None = None

    @property
    def _realm_root(self) -> str:
        return f"{self.settings.base_url}/realms/{quote(self.settings.realm, safe='')}"

    @property
    def _admin_root(self) -> str:
        return f"{self.settings.base_url}/admin/realms/{quote(self.settings.realm, safe='')}"

    def _get_token(self) -> str:
        if self._token:
            return self._token
        try:
            response = self.session.post(
                f"{self._realm_root}/protocol/openid-connect/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.settings.client_id,
                    "client_secret": self.settings.client_secret,
                },
                headers={"Accept": "application/json"},
                timeout=self.settings.timeout_seconds,
            )
        except requests.RequestException as error:
            raise KeycloakTransportError("Keycloak Admin token request failed") from error
        if response.status_code in {401, 403}:
            raise KeycloakAuthError("Keycloak Admin credentials were rejected")
        if response.status_code >= 400:
            raise KeycloakProvisionError(f"Keycloak Admin token request returned HTTP {response.status_code}")
        try:
            token = str(response.json().get("access_token") or "").strip()
        except (AttributeError, TypeError, ValueError) as error:
            raise KeycloakProvisionError("Keycloak Admin token response was invalid") from error
        if not token:
            raise KeycloakProvisionError("Keycloak Admin token response had no access token")
        self._token = token
        return token

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        headers = dict(kwargs.pop("headers", {}) or {})
        headers.update({"Accept": "application/json", "Authorization": f"Bearer {self._get_token()}"})
        try:
            response = self.session.request(
                method,
                f"{self._admin_root}/{path.lstrip('/')}",
                headers=headers,
                timeout=self.settings.timeout_seconds,
                **kwargs,
            )
        except requests.RequestException as error:
            raise KeycloakTransportError(f"Keycloak Admin {method} request failed") from error
        if response.status_code in {401, 403}:
            self._token = None
            raise KeycloakAuthError(f"Keycloak Admin {method} was rejected")
        if response.status_code >= 400:
            raise KeycloakProvisionError(f"Keycloak Admin {method} returned HTTP {response.status_code}")
        return response

    def find_user(self, email: str) -> dict[str, Any] | None:
        response = self._request("GET", "users", params={"email": email, "exact": "true"})
        try:
            users = response.json()
        except (AttributeError, TypeError, ValueError) as error:
            raise KeycloakProvisionError("Keycloak user search response was invalid") from error
        if not isinstance(users, list):
            raise KeycloakProvisionError("Keycloak user search response was not a list")
        for user in users:
            if isinstance(user, dict) and str(user.get("email") or "").casefold() == email.casefold():
                return user
        return None

    def upsert_user(self, email: str, first_name: str, last_name: str) -> str:
        existing = self.find_user(email)
        payload = {
            "username": email,
            "email": email,
            "firstName": first_name,
            "lastName": last_name,
            "enabled": True,
            "emailVerified": False,
        }
        if existing and existing.get("id"):
            user_id = str(existing["id"])
            self._request("PUT", f"users/{quote(user_id, safe='')}", json=payload)
            return user_id

        response = self._request("POST", "users", json=payload)
        location = str(getattr(response, "headers", {}).get("Location") or "")
        user_id = location.rstrip("/").rsplit("/", 1)[-1] if location else ""
        if not user_id:
            try:
                user_id = str(response.json().get("id") or "")
            except (AttributeError, TypeError, ValueError):
                user_id = ""
        if not user_id:
            refreshed = self.find_user(email)
            user_id = str((refreshed or {}).get("id") or "")
        if not user_id:
            raise KeycloakProvisionError("Keycloak created a user without returning an id")
        return user_id

    def send_password_setup(self, user_id: str) -> None:
        self._request(
            "PUT",
            f"users/{quote(user_id, safe='')}/execute-actions-email",
            json=["UPDATE_PASSWORD"],
        )
