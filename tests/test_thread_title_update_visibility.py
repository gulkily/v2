from __future__ import annotations

import os
import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from textwrap import dedent
from unittest import mock

from forum_web.web import application


class ThreadTitleUpdateVisibilityTests(unittest.TestCase):
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
        self.write_record(
            "records/thread-title-updates/thread-title-update-001.txt",
            """
            Record-ID: thread-title-update-001
            Thread-ID: thread-001
            Timestamp: 2026-03-28T12:00:00Z

            Updated title
            """,
        )

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def write_record(self, relative_path: str, raw_text: str) -> None:
        path = self.repo_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(dedent(raw_text).lstrip(), encoding="ascii")

    def request(self, path: str, query_string: str = "") -> tuple[str, dict[str, str], str]:
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

    def test_thread_page_uses_resolved_current_title(self) -> None:
        status, _, body = self.request("/threads/thread-001")

        self.assertEqual(status, "200 OK")
        self.assertIn("Updated title", body)
        self.assertNotIn("<title>Original title</title>", body)

    def test_api_list_index_uses_resolved_current_title(self) -> None:
        status, _, body = self.request("/api/list_index")

        self.assertEqual(status, "200 OK")
        self.assertIn("thread-001\tUpdated title\tgeneral", body)

    def test_api_get_thread_reports_resolved_current_title(self) -> None:
        status, _, body = self.request("/api/get_thread", "thread_id=thread-001")

        self.assertEqual(status, "200 OK")
        self.assertIn("Current-Title: Updated title", body)
        self.assertIn("Subject: Original title", body)
