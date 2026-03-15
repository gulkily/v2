from __future__ import annotations

import json
import os
import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from unittest import mock

from forum_core.llm_provider import LLMProviderError
from forum_read_only.web import application


class LLMApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.tempdir.name)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def request(
        self,
        path: str,
        *,
        method: str = "GET",
        body: bytes = b"",
    ) -> tuple[str, dict[str, str], str]:
        environ = {
            "PATH_INFO": path,
            "QUERY_STRING": "",
            "REQUEST_METHOD": method,
            "CONTENT_LENGTH": str(len(body)),
            "wsgi.input": BytesIO(body),
        }
        response: dict[str, object] = {}

        def start_response(status: str, headers: list[tuple[str, str]]) -> None:
            response["status"] = status
            response["headers"] = headers

        with mock.patch.dict(os.environ, {"FORUM_REPO_ROOT": str(self.repo_root)}):
            body_text = b"".join(application(environ, start_response)).decode("utf-8")

        return response["status"], dict(response["headers"]), body_text

    def test_api_home_lists_call_llm_route(self) -> None:
        status, _, body = self.request("/api/")

        self.assertEqual(status, "200 OK")
        self.assertIn("call_llm", body)
        self.assertIn("/api/call_llm", body)

    def test_api_call_llm_returns_plain_text_result(self) -> None:
        request_body = json.dumps({"prompt": "Reply with ready."}).encode("utf-8")

        with mock.patch("forum_read_only.web.run_llm", return_value="ready"), mock.patch(
            "forum_read_only.web.get_llm_model",
            return_value="openai/gpt-4o-mini",
        ):
            status, headers, body = self.request("/api/call_llm", method="POST", body=request_body)

        self.assertEqual(status, "200 OK")
        self.assertEqual(headers["Content-Type"], "text/plain; charset=utf-8")
        self.assertIn("Command: call_llm", body)
        self.assertIn("Model: openai/gpt-4o-mini", body)
        self.assertTrue(body.endswith("ready\n"))

    def test_api_call_llm_requires_prompt(self) -> None:
        request_body = json.dumps({}).encode("utf-8")

        status, _, body = self.request("/api/call_llm", method="POST", body=request_body)

        self.assertEqual(status, "400 Bad Request")
        self.assertIn("Error-Code: bad_request", body)
        self.assertIn("missing required field: prompt", body)

    def test_api_call_llm_reports_missing_key_as_internal_error(self) -> None:
        request_body = json.dumps({"prompt": "Reply with ready."}).encode("utf-8")

        with mock.patch(
            "forum_read_only.web.run_llm",
            side_effect=LLMProviderError("DEDALUS_API_KEY is not configured."),
        ):
            status, _, body = self.request("/api/call_llm", method="POST", body=request_body)

        self.assertEqual(status, "500 Internal Server Error")
        self.assertIn("Error-Code: internal_error", body)
        self.assertIn("DEDALUS_API_KEY is not configured.", body)


if __name__ == "__main__":
    unittest.main()
