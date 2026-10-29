"""Bitrix24 REST API CLI call tool."""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Mapping

from scripts.bitrix.rest_client import (
    BitrixRestError,
    CallArgs,
    WebhookEndpoint,
    post_json,
    sanitize_text,
)


class ArgumentParsingError(Exception):
    """Raised on CLI argument syntax errors."""


class CustomArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise ArgumentParsingError(message)


def parse_cli_args(argv: list[str]) -> tuple[str, dict[str, Any]]:
    parser = CustomArgumentParser(
        prog="call.py",
        description="Call Bitrix24 REST API method",
        add_help=False,
    )
    parser.add_argument("method", nargs="?", default=None, help="REST method name")
    parser.add_argument("--params", default=None, help="JSON object with parameters")

    args, unknown = parser.parse_known_args(argv)
    if unknown:
        raise ArgumentParsingError(f"Unknown arguments: {' '.join(unknown)}")

    if not args.method:
        raise ArgumentParsingError("Method name is required")

    params: dict[str, Any] = {}
    if args.params is not None:
        try:
            parsed = json.loads(args.params)
        except Exception as exc:
            raise ArgumentParsingError(f"--params must be valid JSON: {exc}") from exc
        if not isinstance(parsed, dict):
            raise ArgumentParsingError("--params must be a JSON object")
        params = parsed

    return args.method, params


def main(
    argv: list[str] | None = None,
    env: Mapping[str, str] | None = None,
    opener: Any = None,
    stdout: Any = None,
    stderr: Any = None,
) -> int:
    if argv is None:
        argv = sys.argv[1:]
    if env is None:
        env = os.environ
    if stdout is None:
        stdout = sys.stdout
    if stderr is None:
        stderr = sys.stderr

    token: str | None = None
    try:
        method, params = parse_cli_args(argv)
        endpoint = WebhookEndpoint.from_env(env)
        token = endpoint.token
        call_args = CallArgs(method=method, params=params)
    except Exception as exc:
        msg = sanitize_text(str(exc), token)
        stderr.write(f"{msg}\n")
        return 2

    try:
        response_bytes = post_json(
            endpoint=endpoint,
            method=call_args.method,
            params=call_args.params,
            opener=opener,
        )
    except BitrixRestError as exc:
        msg = sanitize_text(str(exc), token)
        stderr.write(f"{msg}\n")
        return 1
    except Exception as exc:
        msg = sanitize_text(str(exc), token)
        stderr.write(f"transport_error: {msg}\n")
        return 1

    text = response_bytes.decode("utf-8")
    if not text.endswith("\n"):
        text += "\n"
    stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
