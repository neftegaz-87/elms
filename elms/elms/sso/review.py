"""Guarded hand-off from the ELMS Desk to the first-party review screen."""

from __future__ import annotations

import hashlib
import hmac
import os
import pickle
import re
import secrets
from collections.abc import Mapping
from urllib.parse import urlencode, urlparse

import frappe


DEFAULT_REVIEW_ROLES = frozenset({"ELMS Admin", "ELMS Operations User", "System Manager"})
DEFAULT_REVIEW_ROLE_MAP = {
    "ELMS Admin": "admin",
    "ELMS Operations User": "dispatcher",
    "System Manager": "admin",
}
DEFAULT_HANDOFF_TTL_SECONDS = 60
HANDOFF_CACHE_PREFIX = "elms_review_handoff:"
HANDOFF_TICKET_PATTERN = re.compile(r"^[A-Za-z0-9_-]{32,256}$")


def _configured_roles() -> frozenset[str]:
    raw = os.getenv("ELMS_REVIEW_ELMS_ROLES", "")
    values = {item.strip() for item in raw.split(",") if item.strip()}
    return frozenset(values or DEFAULT_REVIEW_ROLES)


def _review_url() -> str:
    value = os.getenv("ELMS_REVIEW_URL", "").strip().rstrip("/")
    parsed = urlparse(value)
    allow_http = os.getenv("ELMS_REVIEW_ALLOW_HTTP", "0").strip().casefold() in {"1", "true", "yes", "on"}
    allowed_schemes = {"https"} | ({"http"} if allow_http else set())
    if (
        parsed.scheme not in allowed_schemes
        or not parsed.netloc
        or parsed.username
        or parsed.password
        or parsed.fragment
        or any(char in value for char in "\r\n")
    ):
        frappe.throw("Ссылка на экран сверки не настроена администратором.", frappe.ValidationError)
    return value


def _handoff_secret() -> str:
    secret = str(os.getenv("ELMS_REVIEW_HANDOFF_SECRET", "")).strip()
    if not secret:
        frappe.throw("Переход в сверку не настроен администратором.", frappe.ValidationError)
    return secret


def _handoff_ttl() -> int:
    try:
        value = int(os.getenv("ELMS_REVIEW_HANDOFF_TTL_SECONDS", str(DEFAULT_HANDOFF_TTL_SECONDS)))
    except ValueError as error:
        raise ValueError("ELMS_REVIEW_HANDOFF_TTL_SECONDS must be an integer") from error
    if not 1 <= value <= 300:
        raise ValueError("ELMS_REVIEW_HANDOFF_TTL_SECONDS must be between 1 and 300")
    return value


def _review_member_id() -> str:
    return str(os.getenv("ELMS_REVIEW_MEMBER_ID", "elms-dev")).strip() or "elms-dev"


def _role_map() -> dict[str, str]:
    result = dict(DEFAULT_REVIEW_ROLE_MAP)
    raw = str(os.getenv("ELMS_REVIEW_ROLE_MAP", "")).strip()
    if not raw:
        return result
    for item in raw.split(","):
        source, separator, target = item.partition("=")
        if not separator or not source.strip() or not target.strip():
            raise ValueError("ELMS_REVIEW_ROLE_MAP must contain source=target pairs")
        result[source.strip()] = target.strip().casefold()
    return result


def _review_roles(roles: set[str]) -> frozenset[str]:
    configured = _role_map()
    return frozenset(configured[role] for role in roles if role in configured)


def _handoff_key(ticket: str) -> str:
    digest = hashlib.sha256(ticket.encode("utf-8")).hexdigest()
    return f"{HANDOFF_CACHE_PREFIX}{digest}"


def _handoff_location(ticket: str) -> str:
    parsed = urlparse(_review_url())
    return parsed._replace(
        path="/auth/handoff",
        params="",
        query=urlencode({"ticket": ticket}),
        fragment="",
    ).geturl()


def _request_header(name: str) -> str:
    request = getattr(frappe.local, "request", None)
    headers = getattr(request, "headers", None)
    if headers is None:
        return ""
    return str(headers.get(name, "") or "").strip()


def _consume_handoff_ticket(ticket: str) -> dict[str, object] | None:
    cache = frappe.cache()
    raw = cache.getdel(cache.make_key(_handoff_key(ticket)))
    if raw is None:
        return None
    if isinstance(raw, (bytes, bytearray)):
        raw = pickle.loads(raw)
    return dict(raw) if isinstance(raw, Mapping) else None


@frappe.whitelist()
def open_review() -> None:
    """Issue a short-lived one-time ticket after the ELMS role check."""

    user = str(getattr(frappe.session, "user", "") or "").strip()
    if not user or user == "Guest":
        frappe.throw("Войдите в ELMS, чтобы открыть сверку заявки.", frappe.PermissionError)
    roles = set(frappe.get_roles(user) or [])
    allowed_roles = _configured_roles()
    if not roles.intersection(allowed_roles):
        frappe.throw("У вас нет права открывать сверку заявок.", frappe.PermissionError)
    review_roles = _review_roles(roles.intersection(allowed_roles))
    if not review_roles:
        frappe.throw("У вас нет права открывать сверку заявок.", frappe.PermissionError)
    ticket = secrets.token_urlsafe(32)
    frappe.cache().set_value(
        _handoff_key(ticket),
        {
            "user_id": user,
            "member_id": _review_member_id(),
            "roles": sorted(review_roles),
            "return_to": "/queue",
        },
        expires_in_sec=_handoff_ttl(),
    )
    frappe.local.response["type"] = "redirect"
    frappe.local.response["location"] = _handoff_location(ticket)


@frappe.whitelist(allow_guest=True, methods=["POST"])
def redeem_review_handoff(ticket: str | None = None) -> dict[str, object]:
    """Redeem the one-time ticket for the review container over its secret link."""

    configured = _handoff_secret()
    provided = _request_header("X-ELMS-Review-Handoff-Secret")
    if not provided or not hmac.compare_digest(provided, configured):
        frappe.throw("Переход в сверку отклонён.", frappe.PermissionError)
    value = str(ticket or "").strip()
    if not HANDOFF_TICKET_PATTERN.fullmatch(value):
        frappe.throw("Ссылка перехода недействительна или истекла.", frappe.PermissionError)
    payload = _consume_handoff_ticket(value)
    if payload is None:
        frappe.throw("Ссылка перехода недействительна или уже использована.", frappe.PermissionError)
    roles = payload.get("roles")
    user_id = str(payload.get("user_id") or "").strip()
    member_id = str(payload.get("member_id") or "").strip()
    if not user_id or not member_id or not isinstance(roles, list) or not roles:
        frappe.throw("Ссылка перехода недействительна.", frappe.PermissionError)
    return {
        "ok": True,
        "user_id": user_id,
        "member_id": member_id,
        "roles": roles,
        "group_ids": [],
        "return_to": "/queue",
    }


__all__ = ["open_review", "redeem_review_handoff"]
