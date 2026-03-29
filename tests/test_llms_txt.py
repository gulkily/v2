from __future__ import annotations

import os
import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from unittest import mock

from forum_web.web import application


class LlmsTxtTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.tempdir.name)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def request(self, path: str) -> tuple[str, dict[str, str], str]:
        environ = {
            "PATH_INFO": path,
            "QUERY_STRING": "",
            "REQUEST_METHOD": "GET",
            "CONTENT_LENGTH": "0",
            "wsgi.input": BytesIO(b""),
        }
        response: dict[str, object] = {}

        def start_response(status: str, headers: list[tuple[str, str]]) -> None:
            response["status"] = status
            response["headers"] = headers

        with mock.patch.dict(os.environ, {"FORUM_REPO_ROOT": str(self.repo_root)}):
            body = b"".join(application(environ, start_response)).decode("utf-8")

        return response["status"], dict(response["headers"]), body

    def test_llms_txt_describes_machine_and_posting_surfaces(self) -> None:
        status, headers, body = self.request("/llms.txt")

        self.assertEqual(status, "200 OK")
        self.assertEqual(headers["Content-Type"], "text/plain; charset=utf-8")
        self.assertIn("# v2 llms.txt", body)
        self.assertIn("GET /api/", body)
        self.assertIn("POST /api/create_thread", body)
        self.assertIn("POST /api/update_thread_title", body)
        self.assertIn("GET /compose/thread", body)
        self.assertIn("Use /instance/ to inspect current public operator and deployment facts.", body)


if __name__ == "__main__":
    unittest.main()
