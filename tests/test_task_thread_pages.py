from __future__ import annotations

import os
import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from textwrap import dedent
from unittest import mock

from forum_read_only.web import application


class TaskThreadPagesTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.tempdir.name)
        self.write_record(
            "records/posts/T01.txt",
            """
            Post-ID: T01
            Board-Tags: planning
            Subject: Example task thread
            Thread-Type: task
            Task-Status: proposed
            Task-Presentability-Impact: 0.80
            Task-Implementation-Difficulty: 0.35
            Task-Depends-On: T00
            Task-Sources: todo.txt; ideas.txt

            Ship a task thread through the normal discussion flow.
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

    def test_compose_task_page_shows_task_specific_fields(self) -> None:
        status, _, body = self.get("/compose/task")

        self.assertEqual(status, "200 OK")
        self.assertIn("Compose a signed task thread", body)
        self.assertIn('data-thread-type="task"', body)
        self.assertIn('id="task-status-input"', body)
        self.assertIn('id="task-impact-input"', body)
        self.assertIn('id="task-difficulty-input"', body)

    def test_task_thread_page_renders_structured_metadata(self) -> None:
        status, _, body = self.get("/threads/T01")

        self.assertEqual(status, "200 OK")
        self.assertIn("Task metadata", body)
        self.assertIn("This typed root post is the current task record", body)
        self.assertIn("0.80", body)
        self.assertIn("0.35", body)
        self.assertIn("/threads/T00", body)
        self.assertIn("/compose/reply?thread_id=T01&parent_id=T01", body)


if __name__ == "__main__":
    unittest.main()
