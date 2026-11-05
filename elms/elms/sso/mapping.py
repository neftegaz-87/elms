"""SSO identity and email mapping lookup for Bitrix to Yandex 360 / Keycloak."""

from __future__ import annotations

import csv
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DATA_PATH = Path(__file__).resolve().parent / "data" / "email-mapping.csv"


def normalize_email(value: str) -> str:
    if not value or not isinstance(value, str):
        return ""
    return unicodedata.normalize("NFC", value).strip().casefold()


@dataclass(frozen=True, slots=True)
class UserMapping:
    bitrix_id: str
    bitrix_email: str
    full_name: str
    position: str
    departments: str
    corporate_login: str
    yandex_email: str
    role_profile: str
    elms_roles: list[str]
    keycloak_realm_roles: list[str]
    is_priority_target: bool


class IdentityMappingRegistry:
    """Thread-safe in-memory cache of identity mappings between Bitrix and Yandex/Keycloak."""

    def __init__(self, csv_path: Path | None = None) -> None:
        self.csv_path = csv_path or DATA_PATH
        self._by_bitrix_email: dict[str, UserMapping] = {}
        self._by_yandex_email: dict[str, UserMapping] = {}
        self._by_corporate_login: dict[str, UserMapping] = {}
        self._by_bitrix_id: dict[str, UserMapping] = {}
        self._load()

    def _load(self) -> None:
        if not self.csv_path.exists():
            return
        with open(self.csv_path, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                bitrix_id = str(row.get("bitrix_id") or "").strip()
                bitrix_email = normalize_email(row.get("bitrix_email") or "")
                corp_login = str(row.get("target_login") or row.get("corporate_login") or row.get("target_login") or row.get("yandex-login") or row.get("ydx_login") or "").strip().lower()
                yandex_email = normalize_email(row.get("target_email") or row.get("corporate_email") or row.get("yandex_email_template") or row.get("yandex_email") or "")
                full_name = str(row.get("full_name") or "").strip()
                position = str(row.get("position") or "").strip()
                departments = str(row.get("departments") or "").strip()
                role_profile = str(row.get("role_profile") or "").strip()
                elms_roles_raw = str(row.get("elms_roles") or "").strip()
                elms_roles = [r.strip() for r in elms_roles_raw.split(",") if r.strip()]
                kc_roles_raw = str(row.get("keycloak_realm_roles") or "").strip()
                kc_roles = [r.strip() for r in kc_roles_raw.split(",") if r.strip()]
                is_priority = str(row.get("is_priority_target") or "").upper() == "YES"

                mapping = UserMapping(
                    bitrix_id=bitrix_id,
                    bitrix_email=bitrix_email,
                    full_name=full_name,
                    position=position,
                    departments=departments,
                    corporate_login=corp_login,
                    yandex_email=yandex_email,
                    role_profile=role_profile,
                    elms_roles=elms_roles,
                    keycloak_realm_roles=kc_roles,
                    is_priority_target=is_priority,
                )
                if bitrix_email:
                    self._by_bitrix_email[bitrix_email] = mapping
                if yandex_email:
                    self._by_yandex_email[yandex_email] = mapping
                if corp_login:
                    self._by_corporate_login[corp_login] = mapping
                if bitrix_id:
                    self._by_bitrix_id[bitrix_id] = mapping

    def resolve_target_identity(self, identifier: str) -> str:
        """Resolve any given identifier (Bitrix email, Yandex email, Yandex login) to canonical Yandex email."""
        clean = normalize_email(identifier)
        if clean in self._by_bitrix_email:
            return self._by_bitrix_email[clean].yandex_email
        if clean in self._by_yandex_email:
            return self._by_yandex_email[clean].yandex_email
        login_key = identifier.strip().lower()
        if login_key in self._by_corporate_login:
            return self._by_corporate_login[login_key].yandex_email
        return identifier

    def get_mapping(self, identifier: str) -> UserMapping | None:
        clean = normalize_email(identifier)
        if clean in self._by_bitrix_email:
            return self._by_bitrix_email[clean]
        if clean in self._by_yandex_email:
            return self._by_yandex_email[clean]
        login_key = identifier.strip().lower()
        if login_key in self._by_corporate_login:
            return self._by_corporate_login[login_key]
        return None


_DEFAULT_REGISTRY: IdentityMappingRegistry | None = None


def get_mapping_registry() -> IdentityMappingRegistry:
    global _DEFAULT_REGISTRY
    if _DEFAULT_REGISTRY is None:
        _DEFAULT_REGISTRY = IdentityMappingRegistry()
    return _DEFAULT_REGISTRY
