"""Unit tests for Bitrix REST client transport and call CLI."""

from __future__ import annotations

import io
import json
from pathlib import Path
import json
import unittest
import urllib.error
import urllib.request
from typing import Any

from scripts.bitrix import call, scope
from scripts.bitrix.rest_client import (
    BitrixRestError,
    CallArgs,
    WebhookEndpoint,
    post_json,
)


TEST_WEBHOOK_URL = "https://portal.example/rest/1/testkey/"
TEST_ENV = {"BITRIX_REST_WEBHOOK_URL": TEST_WEBHOOK_URL}


class MockResponse:
    """Mock HTTP response object."""

    def __init__(
        self,
        body: bytes,
        status: int = 200,
        headers: dict[str, str] | None = None,
    ) -> None:
        self._body = body
        self.status = status
        self.code = status
        self.headers = headers or {"Content-Type": "application/json"}

    def read(self) -> bytes:
        return self._body

    def getcode(self) -> int:
        return self.status

    def __enter__(self) -> MockResponse:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        pass


class MockOpener:
    """Mock urllib opener recording requests and returning configured response."""

    def __init__(self, response_or_exc: Any = None) -> None:
        self.response_or_exc = response_or_exc
        self.last_request: urllib.request.Request | None = None
        self.call_count = 0

    def open(self, req: urllib.request.Request, timeout: float = 30) -> Any:
        self.call_count += 1
        self.last_request = req
        if isinstance(self.response_or_exc, Exception):
            raise self.response_or_exc
        return self.response_or_exc


class CallSuccessTest(unittest.TestCase):
    """TM-001 / AC-1 / US-001: successful method call tests."""

    def test_call_user_current_success(self) -> None:
        expected_body = b'{"result":{"ID":"1","NAME":"Admin"},"time":{}}'
        opener = MockOpener(MockResponse(expected_body, 200))
        stdout = io.StringIO()
        stderr = io.StringIO()

        exit_code = call.main(
            argv=["user.current"],
            env=TEST_ENV,
            opener=opener,
            stdout=stdout,
            stderr=stderr,
        )

        self.assertEqual(exit_code, 0)
        self.assertIn('"result"', stdout.getvalue())
        self.assertIn('"ID":"1"', stdout.getvalue())
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(opener.call_count, 1)

        req = opener.last_request
        self.assertIsNotNone(req)
        self.assertEqual(
            req.full_url,
            "https://portal.example/rest/1/testkey/user.current.json",
        )
        self.assertEqual(req.get_method(), "POST")
        self.assertEqual(
            req.headers.get("Content-type"),
            "application/json; charset=utf-8",
        )
        self.assertEqual(req.data, b"{}")

    def test_call_with_params(self) -> None:
        expected_body = b'{"result":[{"id":2,"title":"Deal 2"}],"total":1}'
        opener = MockOpener(MockResponse(expected_body, 200))
        stdout = io.StringIO()
        stderr = io.StringIO()

        exit_code = call.main(
            argv=["crm.item.list", "--params", '{"entityTypeId": 2}'],
            env=TEST_ENV,
            opener=opener,
            stdout=stdout,
            stderr=stderr,
        )

        self.assertEqual(exit_code, 0)
        self.assertIn('"Deal 2"', stdout.getvalue())
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(opener.call_count, 1)

        req = opener.last_request
        self.assertIsNotNone(req)
        self.assertEqual(
            req.full_url,
            "https://portal.example/rest/1/testkey/crm.item.list.json",
        )
        self.assertEqual(json.loads(req.data.decode("utf-8")), {"entityTypeId": 2})


class CallBitrixErrorTest(unittest.TestCase):
    """TM-002 / AC-2 / BN-006: portal error envelope tests."""

    def test_error_envelope_200(self) -> None:
        error_body = (
            b'{"error":"insufficient_scope","error_description":"Need crm scope"}'
        )
        opener = MockOpener(MockResponse(error_body, 200))
        stdout = io.StringIO()
        stderr = io.StringIO()

        exit_code = call.main(
            argv=["crm.deal.get"],
            env=TEST_ENV,
            opener=opener,
            stdout=stdout,
            stderr=stderr,
        )

        self.assertEqual(exit_code, 1)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("insufficient_scope", stderr.getvalue())
        self.assertIn("Need crm scope", stderr.getvalue())

    def test_error_envelope_http_error(self) -> None:
        error_body = (
            b'{"error":"insufficient_scope","error_description":"Token invalid: testkey"}'
        )
        http_err = urllib.error.HTTPError(
            url="https://portal.example/rest/1/testkey/crm.deal.get.json",
            code=401,
            msg="Unauthorized",
            hdrs={},  # type: ignore[arg-type]
            fp=io.BytesIO(error_body),
        )
        opener = MockOpener(http_err)
        stdout = io.StringIO()
        stderr = io.StringIO()

        exit_code = call.main(
            argv=["crm.deal.get"],
            env=TEST_ENV,
            opener=opener,
            stdout=stdout,
            stderr=stderr,
        )

        self.assertEqual(exit_code, 1)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("insufficient_scope", stderr.getvalue())
        # Secret token 'testkey' must be sanitized from error output
        self.assertNotIn("testkey", stderr.getvalue())
        self.assertIn("***", stderr.getvalue())


class MissingWebhookTest(unittest.TestCase):
    """TM-003 / AC-3 / BN-001 / BN-002: missing or invalid env webhook URL."""

    def test_missing_env_variable(self) -> None:
        opener = MockOpener()
        stdout = io.StringIO()
        stderr = io.StringIO()

        exit_code = call.main(
            argv=["user.current"],
            env={},
            opener=opener,
            stdout=stdout,
            stderr=stderr,
        )

        self.assertEqual(exit_code, 2)
        self.assertIn("BITRIX_REST_WEBHOOK_URL", stderr.getvalue())
        self.assertEqual(stdout.getvalue(), "")
        self.assertEqual(opener.call_count, 0)

    def test_only_board_webhook_url_present(self) -> None:
        opener = MockOpener()
        stdout = io.StringIO()
        stderr = io.StringIO()

        exit_code = call.main(
            argv=["user.current"],
            env={"BITRIX_WEBHOOK_URL": "https://board.example/webhook/key"},
            opener=opener,
            stdout=stdout,
            stderr=stderr,
        )

        self.assertEqual(exit_code, 2)
        self.assertIn("BITRIX_REST_WEBHOOK_URL", stderr.getvalue())
        self.assertNotIn("board.example", stderr.getvalue())
        self.assertEqual(stdout.getvalue(), "")
        self.assertEqual(opener.call_count, 0)

    def test_empty_env_variable(self) -> None:
        opener = MockOpener()
        stdout = io.StringIO()
        stderr = io.StringIO()

        exit_code = call.main(
            argv=["user.current"],
            env={"BITRIX_REST_WEBHOOK_URL": "   "},
            opener=opener,
            stdout=stdout,
            stderr=stderr,
        )

        self.assertEqual(exit_code, 2)
        self.assertIn("BITRIX_REST_WEBHOOK_URL", stderr.getvalue())
        self.assertEqual(opener.call_count, 0)


class BadWebhookUrlTest(unittest.TestCase):
    """TM-004 / BN-003: invalid URL format fails before HTTP."""

    def _assert_bad_url(self, bad_url: str) -> None:
        opener = MockOpener()
        stdout = io.StringIO()
        stderr = io.StringIO()

        exit_code = call.main(
            argv=["user.current"],
            env={"BITRIX_REST_WEBHOOK_URL": bad_url},
            opener=opener,
            stdout=stdout,
            stderr=stderr,
        )

        self.assertEqual(exit_code, 2, f"Expected exit 2 for URL {bad_url}")
        self.assertEqual(opener.call_count, 0)
        self.assertEqual(stdout.getvalue(), "")

    def test_non_https(self) -> None:
        self._assert_bad_url("http://portal.example/rest/1/testkey/")

    def test_url_with_method_tail(self) -> None:
        self._assert_bad_url("https://portal.example/rest/1/testkey/user.current")

    def test_first_segment_not_rest(self) -> None:
        self._assert_bad_url("https://portal.example/api/1/testkey/")

    def test_user_id_not_digits(self) -> None:
        self._assert_bad_url("https://portal.example/rest/notdigits/testkey/")

    def test_missing_token_segment(self) -> None:
        self._assert_bad_url("https://portal.example/rest/1/")


class BadArgsTest(unittest.TestCase):
    """TM-005 / BN-004 / FR-006 / FR-007: invalid method or parameters."""

    def _assert_bad_args(self, argv: list[str]) -> None:
        opener = MockOpener()
        stdout = io.StringIO()
        stderr = io.StringIO()

        exit_code = call.main(
            argv=argv,
            env=TEST_ENV,
            opener=opener,
            stdout=stdout,
            stderr=stderr,
        )

        self.assertEqual(exit_code, 2, f"Expected exit 2 for argv {argv}")
        self.assertEqual(opener.call_count, 0)
        self.assertEqual(stdout.getvalue(), "")

    def test_uppercase_method(self) -> None:
        self._assert_bad_args(["User.Current"])

    def test_method_without_dot(self) -> None:
        self._assert_bad_args(["user"])

    def test_method_double_dot(self) -> None:
        self._assert_bad_args(["user..current"])

    def test_method_length_exceeded(self) -> None:
        self._assert_bad_args(["user." + ("a" * 125)])

    def test_missing_method(self) -> None:
        self._assert_bad_args([])

    def test_params_array(self) -> None:
        self._assert_bad_args(["user.current", "--params", "[]"])

    def test_params_string(self) -> None:
        self._assert_bad_args(["user.current", "--params", '"value"'])

    def test_params_number(self) -> None:
        self._assert_bad_args(["user.current", "--params", "123"])

    def test_params_malformed_json(self) -> None:
        self._assert_bad_args(["user.current", "--params", "{broken"])

    def test_unknown_cli_flag(self) -> None:
        self._assert_bad_args(["user.current", "--invalid-flag"])


class BatchGuardTest(unittest.TestCase):
    """TM-006 / BN-005 / FR-008: batch limit and nesting guards."""

    def test_batch_length_exceeded_dict(self) -> None:
        cmd_dict = {f"cmd_{i}": "user.current" for i in range(51)}
        opener = MockOpener()
        stdout = io.StringIO()
        stderr = io.StringIO()

        exit_code = call.main(
            argv=["batch", "--params", json.dumps({"cmd": cmd_dict})],
            env=TEST_ENV,
            opener=opener,
            stdout=stdout,
            stderr=stderr,
        )

        self.assertEqual(exit_code, 2)
        self.assertIn("ERROR_BATCH_LENGTH_EXCEEDED", stderr.getvalue())
        self.assertEqual(opener.call_count, 0)

    def test_batch_length_exceeded_list(self) -> None:
        cmd_list = ["user.current"] * 51
        opener = MockOpener()
        stdout = io.StringIO()
        stderr = io.StringIO()

        exit_code = call.main(
            argv=["batch", "--params", json.dumps({"cmd": cmd_list})],
            env=TEST_ENV,
            opener=opener,
            stdout=stdout,
            stderr=stderr,
        )

        self.assertEqual(exit_code, 2)
        self.assertIn("ERROR_BATCH_LENGTH_EXCEEDED", stderr.getvalue())
        self.assertEqual(opener.call_count, 0)

    def test_batch_nested_not_allowed_dict(self) -> None:
        cmd_dict = {"get_user": "user.current", "nested": "batch?cmd=..."}
        opener = MockOpener()
        stdout = io.StringIO()
        stderr = io.StringIO()

        exit_code = call.main(
            argv=["batch", "--params", json.dumps({"cmd": cmd_dict})],
            env=TEST_ENV,
            opener=opener,
            stdout=stdout,
            stderr=stderr,
        )

        self.assertEqual(exit_code, 2)
        self.assertIn("ERROR_BATCH_METHOD_NOT_ALLOWED", stderr.getvalue())
        self.assertEqual(opener.call_count, 0)

    def test_batch_nested_not_allowed_list(self) -> None:
        cmd_list = ["user.current", "batch.method"]
        opener = MockOpener()
        stdout = io.StringIO()
        stderr = io.StringIO()

        exit_code = call.main(
            argv=["batch", "--params", json.dumps({"cmd": cmd_list})],
            env=TEST_ENV,
            opener=opener,
            stdout=stdout,
            stderr=stderr,
        )

        self.assertEqual(exit_code, 2)
        self.assertIn("ERROR_BATCH_METHOD_NOT_ALLOWED", stderr.getvalue())
        self.assertEqual(opener.call_count, 0)

    def test_batch_valid_success(self) -> None:
        valid_cmd = {"u": "user.current", "d": "crm.deal.get"}
        opener = MockOpener(MockResponse(b'{"result":{"result":{}},"time":{}}', 200))
        stdout = io.StringIO()
        stderr = io.StringIO()

        exit_code = call.main(
            argv=["batch", "--params", json.dumps({"cmd": valid_cmd})],
            env=TEST_ENV,
            opener=opener,
            stdout=stdout,
            stderr=stderr,
        )

        self.assertEqual(exit_code, 0)
        self.assertEqual(opener.call_count, 1)
        self.assertIn('"result"', stdout.getvalue())


class TransportFailureTest(unittest.TestCase):
    """TM-007 / BN-007: non-JSON responses and network transport failures."""

    def test_http_500_non_json(self) -> None:
        http_err = urllib.error.HTTPError(
            url="https://portal.example/rest/1/testkey/user.current.json",
            code=500,
            msg="Internal Server Error",
            hdrs={},  # type: ignore[arg-type]
            fp=io.BytesIO(b"<html>500 Internal Server Error</html>"),
        )
        opener = MockOpener(http_err)
        stdout = io.StringIO()
        stderr = io.StringIO()

        exit_code = call.main(
            argv=["user.current"],
            env=TEST_ENV,
            opener=opener,
            stdout=stdout,
            stderr=stderr,
        )

        self.assertEqual(exit_code, 1)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("500", stderr.getvalue())
        self.assertNotIn("testkey", stderr.getvalue())

    def test_http_200_invalid_json(self) -> None:
        opener = MockOpener(MockResponse(b"not-json-content", 200))
        stdout = io.StringIO()
        stderr = io.StringIO()

        exit_code = call.main(
            argv=["user.current"],
            env=TEST_ENV,
            opener=opener,
            stdout=stdout,
            stderr=stderr,
        )

        self.assertEqual(exit_code, 1)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("invalid_json", stderr.getvalue())

    def test_network_url_error(self) -> None:
        url_err = urllib.error.URLError("Connection refused to testkey server")
        opener = MockOpener(url_err)
        stdout = io.StringIO()
        stderr = io.StringIO()

        exit_code = call.main(
            argv=["user.current"],
            env=TEST_ENV,
            opener=opener,
            stdout=stdout,
            stderr=stderr,
        )

        self.assertEqual(exit_code, 1)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("transport_error", stderr.getvalue())
        # Secret token must not be in stderr
        self.assertNotIn("testkey", stderr.getvalue())


class ScopeFullTest(unittest.TestCase):
    """TM-008 / AC-4 / FR-004 / US-002: scope inspection CLI and --full flag."""

    def test_scope_default_without_flag(self) -> None:
        expected_body = b'{"result":["crm","user"],"time":{}}'
        opener = MockOpener(MockResponse(expected_body, 200))
        stdout = io.StringIO()
        stderr = io.StringIO()

        exit_code = scope.main(
            argv=[],
            env=TEST_ENV,
            opener=opener,
            stdout=stdout,
            stderr=stderr,
        )

        self.assertEqual(exit_code, 0)
        self.assertIn('"crm"', stdout.getvalue())
        self.assertIn('"user"', stdout.getvalue())
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(opener.call_count, 1)

        req = opener.last_request
        self.assertIsNotNone(req)
        self.assertEqual(
            req.full_url,
            "https://portal.example/rest/1/testkey/scope.json",
        )
        self.assertEqual(req.get_method(), "POST")
        self.assertEqual(req.data, b"{}")

    def test_scope_full_flag(self) -> None:
        expected_body = b'{"result":["bizproc","crm","disk","user"],"time":{}}'
        opener = MockOpener(MockResponse(expected_body, 200))
        stdout = io.StringIO()
        stderr = io.StringIO()

        exit_code = scope.main(
            argv=["--full"],
            env=TEST_ENV,
            opener=opener,
            stdout=stdout,
            stderr=stderr,
        )

        self.assertEqual(exit_code, 0)
        self.assertIn('"bizproc"', stdout.getvalue())
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(opener.call_count, 1)

        req = opener.last_request
        self.assertIsNotNone(req)
        self.assertEqual(
            req.full_url,
            "https://portal.example/rest/1/testkey/scope.json",
        )
        self.assertEqual(req.get_method(), "POST")
        self.assertEqual(json.loads(req.data.decode("utf-8")), {"full": True})

    def test_scope_error_envelope(self) -> None:
        error_body = b'{"error":"insufficient_scope","error_description":"Scope error"}'
        opener = MockOpener(MockResponse(error_body, 200))
        stdout = io.StringIO()
        stderr = io.StringIO()

        exit_code = scope.main(
            argv=[],
            env=TEST_ENV,
            opener=opener,
            stdout=stdout,
            stderr=stderr,
        )

        self.assertEqual(exit_code, 1)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("insufficient_scope", stderr.getvalue())

    def test_scope_missing_env(self) -> None:
        opener = MockOpener()
        stdout = io.StringIO()
        stderr = io.StringIO()

        exit_code = scope.main(
            argv=[],
            env={},
            opener=opener,
            stdout=stdout,
            stderr=stderr,
        )

        self.assertEqual(exit_code, 2)
        self.assertIn("BITRIX_REST_WEBHOOK_URL", stderr.getvalue())
        self.assertEqual(opener.call_count, 0)

    def test_scope_unknown_args(self) -> None:
        opener = MockOpener()
        stdout = io.StringIO()
        stderr = io.StringIO()

        exit_code = scope.main(
            argv=["--unknown"],
            env=TEST_ENV,
            opener=opener,
            stdout=stdout,
            stderr=stderr,
        )

        self.assertEqual(exit_code, 2)
        self.assertIn("Unknown arguments", stderr.getvalue())
        self.assertEqual(opener.call_count, 0)



class InstructionTest(unittest.TestCase):
    """TM-009 / AC-5 / FR-005 / FR-009 / US-003: documentation and env template tests."""

    def setUp(self) -> None:
        self.repo_root = Path(__file__).resolve().parent.parent.parent
        self.doc_path = self.repo_root / "docs" / "bitrix-incoming-webhook.md"
        self.env_example_path = self.repo_root / ".env.example"

    def test_doc_exists_and_contains_required_sections(self) -> None:
        self.assertTrue(
            self.doc_path.exists(),
            f"Missing documentation file: {self.doc_path}",
        )
        content = self.doc_path.read_text(encoding="utf-8")
        self.assertIn("Входящий вебхук", content)
        self.assertIn("BITRIX_REST_WEBHOOK_URL", content)
        self.assertIn("BITRIX_WEBHOOK_URL", content)
        self.assertIn("Приложения", content)
        self.assertIn("Разработчикам", content)
        self.assertIn("scope.py", content)
        self.assertIn("call.py", content)
        self.assertIn("Это не `BITRIX_WEBHOOK_URL`", content)

    def test_env_example_contains_webhook_url_and_warning(self) -> None:
        self.assertTrue(
            self.env_example_path.exists(),
            f"Missing .env.example: {self.env_example_path}",
        )
        content = self.env_example_path.read_text(encoding="utf-8")
        self.assertIn("BITRIX_REST_WEBHOOK_URL=", content)
        self.assertIn("Не путать с BITRIX_WEBHOOK_URL доски", content)


if __name__ == "__main__":
    unittest.main()
