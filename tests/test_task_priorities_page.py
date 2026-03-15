from __future__ import annotations

import os
import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from textwrap import dedent
from unittest import mock

from forum_read_only.web import application


class TaskPrioritiesPageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.tempdir.name)
        self.write_record(
            "records/posts/root-001.txt",
            """
            Post-ID: root-001
            Board-Tags: general
            Subject: Hello world

            Root post body.
            """,
        )
        self.write_record(
            "records/tasks/task-t01.txt",
            """
            Task-ID: T01
            Title: Linked task discussion
            Status: proposed
            Presentability-Impact: 0.80
            Implementation-Difficulty: 0.25
            Discussion-Thread-ID: root-001
            Sources: todo.txt; ideas.txt

            One task with a linked discussion thread.
            """,
        )
        self.write_record(
            "records/tasks/task-t02.txt",
            """
            Task-ID: T02
            Title: Unlinked task
            Status: proposed
            Presentability-Impact: 0.55
            Implementation-Difficulty: 0.40
            Depends-On: T01
            Sources: todo.txt

            One task without a linked discussion thread yet.
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

        return (
            response["status"],
            dict(response["headers"]),
            body,
        )

    def test_board_index_links_to_task_priorities_page(self) -> None:
        status, _, body = self.get("/")

        self.assertEqual(status, "200 OK")
        self.assertIn('/planning/task-priorities/', body)
        self.assertIn("task priorities", body)

    def test_task_priorities_page_renders_sortable_table(self) -> None:
        status, headers, body = self.get("/planning/task-priorities/")

        self.assertEqual(status, "200 OK")
        self.assertEqual(headers["Content-Type"], "text/html; charset=utf-8")
        self.assertIn("Development task priorities", body)
        self.assertIn('data-sortable-table', body)
        self.assertIn("Presentability impact", body)
        self.assertIn("Implementation difficulty", body)
        self.assertIn("/planning/tasks/T01", body)
        self.assertIn("/threads/root-001", body)
        self.assertIn("Not linked yet", body)

    def test_task_detail_page_shows_linked_discussion_actions(self) -> None:
        status, headers, body = self.get("/planning/tasks/T01")

        self.assertEqual(status, "200 OK")
        self.assertEqual(headers["Content-Type"], "text/html; charset=utf-8")
        self.assertIn("Linked task discussion", body)
        self.assertIn("/threads/root-001", body)
        self.assertIn("/compose/reply?thread_id=root-001&parent_id=root-001", body)

    def test_task_detail_page_handles_unlinked_tasks(self) -> None:
        status, _, body = self.get("/planning/tasks/T02")

        self.assertEqual(status, "200 OK")
        self.assertIn("does not link to a discussion thread yet", body)
        self.assertIn("/planning/tasks/T01", body)

    def test_unknown_task_returns_404(self) -> None:
        status, _, body = self.get("/planning/tasks/T99")

        self.assertEqual(status, "404 Not Found")
        self.assertIn("could not be located", body)


if __name__ == "__main__":
    unittest.main()
