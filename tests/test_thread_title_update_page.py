from __future__ import annotations

import os
import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from textwrap import dedent
from unittest import mock

from forum_web.web import application


class ThreadTitleUpdatePageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.tempdir.name)
        self.write_record(
            "records/posts/thread-001.txt",
            """
            Post-ID: thread-001
            Board-Tags: general
            Subject: Original title

            Root body.
            """,
        )

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def write_record(self, relative_path: str, raw_text: str) -> None:
        path = self.repo_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(dedent(raw_text).lstrip(), encoding="ascii")

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

        return response["status"], dict(response["headers"]), body

    def test_thread_page_links_to_title_update_flow(self) -> None:
        status, _, body = self.get("/threads/thread-001")

        self.assertEqual(status, "200 OK")
        self.assertIn('href="/threads/thread-001/title"', body)
        self.assertIn(">change title<", body)

    def test_thread_title_update_page_renders_signing_flow(self) -> None:
        status, _, body = self.get("/threads/thread-001/title")

        self.assertEqual(status, "200 OK")
        self.assertIn('id="thread-title-update-app"', body)
        self.assertIn('data-command="update_thread_title"', body)
        self.assertIn('data-endpoint="/api/update_thread_title"', body)
        self.assertIn('id="thread-title-update-form"', body)
        self.assertIn('id="thread-title-input" name="title" type="text" maxlength="72" value="" required', body)
        self.assertIn("Submit title change", body)
        self.assertIn("Current title:", body)
        self.assertIn("Thread-ID:", body)
        self.assertIn("Server accepts the change only when the signing key belongs to the thread owner", body)
        self.assertIn('href="/threads/thread-001"', body)
        self.assertIn('/assets/browser_signing.js', body)


if __name__ == "__main__":
    unittest.main()
