from __future__ import annotations

import os
import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from textwrap import dedent
from unittest import mock

from forum_web.web import application


class SiteActivityPageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.tempdir.name)
        self.write_record(
            "records/posts/root-010.txt",
            """
            Post-ID: root-010
            Board-Tags: general
            Subject: First root

            Root body.
            """,
        )
        self.write_record(
            "records/posts/reply-020.txt",
            """
            Post-ID: reply-020
            Board-Tags: general
            Thread-ID: root-010
            Parent-ID: root-010

            Reply body.
            """,
        )

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def write_record(self, relative_path: str, raw_text: str) -> None:
        path = self.repo_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(dedent(raw_text).lstrip(), encoding="ascii")

    def get(self, path: str) -> tuple[str, dict[str, str], str]:
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

    def test_activity_page_renders_records_and_metadata(self) -> None:
        status, headers, body = self.get("/activity/")

        self.assertEqual(status, "200 OK")
        self.assertEqual(headers["Content-Type"], "text/html; charset=utf-8")
        self.assertIn("Canonical activity stream", body)
        self.assertIn('class="post-card"', body)
        self.assertIn("First root", body)
        self.assertIn("root-010", body)
        self.assertIn("reply-020", body)
        self.assertIn("Commit", body)
        self.assertIn("unknown", body)
        self.assertIn("records/instance/public.txt", body)
        self.assertIn("Working tree", body)
        self.assertIn("git status unavailable", body)


if __name__ == "__main__":
    unittest.main()
