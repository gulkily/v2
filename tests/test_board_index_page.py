from __future__ import annotations

import os
import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from textwrap import dedent
from unittest import mock

from forum_web.web import application


class BoardIndexPageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.tempdir.name)
        self.write_record(
            "records/posts/root-001.txt",
            """
            Post-ID: root-001
            Board-Tags: general meta
            Subject: Hello world

            First line preview.
            Second line body.
            """,
        )
        self.write_record(
            "records/posts/root-002.txt",
            """
            Post-ID: root-002
            Board-Tags: planning
            Subject: Planning thread
            Thread-Type: task
            Task-Status: proposed
            Task-Presentability-Impact: 0.80
            Task-Implementation-Difficulty: 0.30
            Task-Sources: todo.txt

            Planning preview.
            """,
        )
        self.write_record(
            "records/posts/reply-001.txt",
            """
            Post-ID: reply-001
            Board-Tags: general
            Thread-ID: root-001
            Parent-ID: root-001

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

    def test_board_index_uses_front_page_layout(self) -> None:
        status, headers, body = self.get("/")

        self.assertEqual(status, "200 OK")
        self.assertEqual(headers["Content-Type"], "text/html; charset=utf-8")
        self.assertIn('class="front-header"', body)
        self.assertIn('class="front-layout"', body)
        self.assertIn("Threads worth opening", body)
        self.assertIn("/threads/root-001", body)
        self.assertIn("Hello world", body)
        self.assertIn("First line preview.", body)
        self.assertNotIn('class="front-topic-strip"', body)
        self.assertNotIn("What this view is", body)
        self.assertNotIn("House style", body)
        self.assertNotIn("Browse by board tag", body)
        self.assertNotIn('class="front-board-directory"', body)

    def test_board_index_preserves_key_destination_links(self) -> None:
        status, _, body = self.get("/")

        self.assertEqual(status, "200 OK")
        self.assertIn('/compose/thread', body)
        self.assertIn('/instance/', body)
        self.assertIn('/activity/', body)
        self.assertIn('view site activity', body)
        self.assertNotIn('view moderation log', body)
        self.assertIn('/moderation/', body)
        self.assertIn('/planning/task-priorities/', body)


if __name__ == "__main__":
    unittest.main()
