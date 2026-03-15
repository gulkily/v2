from __future__ import annotations

import os
import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from unittest import mock

from forum_read_only.web import application


class ComposeThreadPageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.tempdir.name)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def get(self, path: str, query_string: str = "") -> tuple[str, dict[str, str], str]:
        environ = {
            "PATH_INFO": path,
            "QUERY_STRING": query_string,
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

        return (
            response["status"],
            dict(response["headers"]),
            body,
        )

    def test_compose_thread_page_renders_shared_draft_status_hook(self) -> None:
        status, _, body = self.get("/compose/thread")

        self.assertEqual(status, "200 OK")
        self.assertIn("Compose a signed thread", body)
        self.assertIn('id="signed-post-form"', body)
        self.assertIn('id="draft-status"', body)
        self.assertIn('data-command="create_thread"', body)
        self.assertIn('data-thread-type=""', body)


if __name__ == "__main__":
    unittest.main()
