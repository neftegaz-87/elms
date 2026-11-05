#!/usr/bin/env python3
"""Sync Bitrix24 users to Keycloak based on an identity mapping file."""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

DEFAULT_MAPPING_PATH = PROJECT_ROOT / "elms" / "elms" / "sso" / "data" / "email-mapping.csv"


class KeycloakAdminClient:
    """Minimal Keycloak Admin REST API client."""

    def __init__(self, base_url: str, realm: str = "elms"):
        self.base_url = base_url.rstrip("/")
        self.realm = realm
        self.token: str | None = None

    def authenticate(self, username: str, password: str) -> None:
        token_url = f"{self.base_url}/realms/master/protocol/openid-connect/token"
        data = urlencode({
            "client_id": "admin-cli",
            "grant_type": "password",
            "username": username,
            "password": password,
        }).encode("utf-8")
        req = Request(token_url, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
        with urlopen(req, timeout=10) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
            self.token = payload["access_token"]

    def _api_request(self, endpoint: str, method: str = "GET", data: dict | None = None) -> list | dict:
        url = f"{self.base_url}/admin/realms/{self.realm}/{endpoint.lstrip('/')}"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        encoded_data = json.dumps(data).encode("utf-8") if data is not None else None
        req = Request(url, data=encoded_data, headers=headers, method=method)
        with urlopen(req, timeout=10) as resp:
            content = resp.read()
            if not content:
                return {}
            return json.loads(content.decode("utf-8"))

    def find_user_by_email(self, email: str) -> dict | None:
        users = self._api_request(f"users?email={email}&exact=true")
        if isinstance(users, list) and users:
            return users[0]
        return None

    def create_user(self, payload: dict) -> str:
        url = f"{self.base_url}/admin/realms/{self.realm}/users"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        req = Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
        with urlopen(req, timeout=10) as resp:
            location = resp.headers.get("Location")
            if location:
                return location.rstrip("/").split("/")[-1]
        user = self.find_user_by_email(payload["email"])
        return user["id"] if user else ""

    def update_user(self, user_id: str, payload: dict) -> None:
        self._api_request(f"users/{user_id}", method="PUT", data=payload)


def load_mapping(mapping_path: Path) -> dict[str, dict]:
    """Load CSV mapping: {bitrix_user_id: {yandex_email, status, bitrix_email, roles, ...}}."""
    if not mapping_path.exists():
        raise FileNotFoundError(f"Mapping file not found: {mapping_path}")

    mapping: dict[str, dict] = {}
    with open(mapping_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            b_id = str(row.get("bitrix_id") or row.get("bitrix_user_id") or "").strip()
            if not b_id:
                continue
            b_email = str(row.get("bitrix_email") or "").strip().lower()
            ydx_email = str(row.get("target_email") or row.get("corporate_email") or row.get("yandex_email") or "").strip().lower()
            kc_roles_raw = str(row.get("keycloak_realm_roles") or "employee").strip()
            kc_roles = [r.strip() for r in kc_roles_raw.split(",") if r.strip()]

            mapping[b_id] = {
                "bitrix_email": b_email,
                "yandex_email": ydx_email,
                "full_name": str(row.get("full_name") or "").strip(),
                "status": "active",
                "keycloak_roles": kc_roles or ["employee"],
            }
    return mapping


def fetch_bitrix_users(webhook_url: str) -> list[dict]:
    """Fetch active users from Bitrix24."""
    from scripts.bitrix.rest_client import WebhookEndpoint, post_json

    endpoint = WebhookEndpoint(url=webhook_url)
    resp_bytes = post_json(endpoint, "user.get", {"ACTIVE": "Y"})
    data = json.loads(resp_bytes.decode("utf-8"))
    return data.get("result", [])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Синхронизация пользователей Битрикс24 в Keycloak")
    parser.add_argument(
        "--mapping",
        type=Path,
        default=DEFAULT_MAPPING_PATH,
        help="Путь к CSV маппинга (по умолчанию elms/elms/sso/data/email-mapping.csv)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Только аудит без изменения базы Keycloak")
    parser.add_argument("--apply", action="store_true", help="Реальное применение в Keycloak")
    args = parser.parse_args(argv)

    if not args.dry_run and not args.apply:
        print("Укажите --dry-run для проверки или --apply для выполнения.")
        return 1

    mapping = load_mapping(args.mapping)
    print(f"Загружено записей маппинга: {len(mapping)}")

    webhook_url = os.getenv("BITRIX_REST_WEBHOOK_URL")
    if not webhook_url:
        print("Внимание: BITRIX_REST_WEBHOOK_URL не задан в окружении.", file=sys.stderr)
        print("Синхронизация выполняется по локальному реестру маппинга.", file=sys.stderr)
        bx_users = [
            {
                "ID": b_id,
                "EMAIL": item["bitrix_email"],
                "NAME": item["full_name"],
                "UF_DEPARTMENT": [],
            }
            for b_id, item in mapping.items()
        ]
    else:
        bx_users = fetch_bitrix_users(webhook_url)
        print(f"Получено активных пользователей Битрикс24: {len(bx_users)}")

    kc_url = os.getenv("KEYCLOAK_INTERNAL_URL", "http://127.0.0.1:8480")
    kc_admin = os.getenv("KEYCLOAK_ADMIN", "admin")
    kc_password = os.getenv("KEYCLOAK_ADMIN_PASSWORD", "admin")

    kc = None
    if args.apply:
        kc = KeycloakAdminClient(base_url=kc_url)
        try:
            kc.authenticate(kc_admin, kc_password)
        except Exception as e:
            print(f"Ошибка авторизации в Keycloak Admin API ({kc_url}): {e}", file=sys.stderr)
            return 2

    created_count = 0
    updated_count = 0
    skipped_count = 0

    for u in bx_users:
        b_id = str(u["ID"])
        if b_id not in mapping:
            print(f"Пропуск: пользователь Bitrix ID {b_id} ({u.get('EMAIL')}) отсутствует в маппинге")
            skipped_count += 1
            continue

        item = mapping[b_id]
        if item.get("status") != "active":
            skipped_count += 1
            continue

        yandex_email = item["yandex_email"]
        if not yandex_email:
            skipped_count += 1
            continue

        dep_ids = [str(d) for d in u.get("UF_DEPARTMENT", [])]
        first_name = u.get("NAME") or item["full_name"]
        last_name = u.get("LAST_NAME", "")

        user_payload = {
            "username": yandex_email,
            "email": yandex_email,
            "enabled": True,
            "emailVerified": True,
            "firstName": first_name,
            "lastName": last_name,
            "attributes": {
                "bitrix_user_id": [b_id],
                "bitrix_email": [u.get("EMAIL", item["bitrix_email"])],
                "bitrix_department_ids": dep_ids,
            },
            "realmRoles": item["keycloak_roles"],
        }

        if args.dry_run:
            print(f"[DRY-RUN] Bitrix ID {b_id} ({item['bitrix_email']}) -> Keycloak: {yandex_email} (roles={item['keycloak_roles']})")
            updated_count += 1
            continue

        if kc:
            existing_user = kc.find_user_by_email(yandex_email)
            if existing_user:
                print(f"[UPDATE] Bitrix ID {b_id} -> Keycloak user {yandex_email}")
                user_payload["id"] = existing_user["id"]
                kc.update_user(existing_user["id"], user_payload)
                updated_count += 1
            else:
                print(f"[CREATE] Bitrix ID {b_id} -> Новый Keycloak user {yandex_email}")
                kc.create_user(user_payload)
                created_count += 1

    mode = "DRY-RUN" if args.dry_run else "APPLIED"
    print(f'\n[{mode}] Итог: Создано={created_count}, Обновлено={updated_count}, Пропущено={skipped_count}')
    return 0


if __name__ == "__main__":
    sys.exit(main())
