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
            "records/posts/T01.txt",
            """
            Post-ID: T01
            Board-Tags: planning
            Subject: First task thread
            Thread-Type: task
            Task-Status: proposed
            Task-Presentability-Impact: 0.80
            Task-Implementation-Difficulty: 0.25
            Task-Sources: todo.txt; ideas.txt

            One task thread with a visible reply.
            """,
        )
        self.write_record(
            "records/posts/T02.txt",
            """
            Post-ID: T02
            Board-Tags: planning
            Subject: Second task thread
            Thread-Type: task
            Task-Status: proposed
            Task-Presentability-Impact: 0.55
            Task-Implementation-Difficulty: 0.40
            Task-Depends-On: T01
            Task-Sources: todo.txt

            One task thread that depends on the first task.
            """,
        )
        self.write_record(
            "records/posts/T03.txt",
            """
            Post-ID: T03
            Board-Tags: planning
            Subject: Third task thread
            Thread-Type: task
            Task-Status: done
            Task-Presentability-Impact: 0.20
            Task-Implementation-Difficulty: 0.10
            Task-Sources: notes.txt

            One completed task thread.
            """,
        )
        self.write_record(
            "records/posts/reply-001.txt",
            """
            Post-ID: reply-001
            Board-Tags: planning
            Thread-ID: T01
            Parent-ID: T01

            First task comment.
            """,
        )
        self.write_record(
            "records/posts/proposal-001.txt",
            """
            Post-ID: proposal-001
            Board-Tags: planning
            Subject: Future typed root
            Thread-Type: proposal

            This should not appear in task planning surfaces.
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
        self.assertIn("Open task table", body)
        self.assertIn('data-sortable-table', body)
        self.assertIn("Presentability impact", body)
        self.assertIn("Implementation difficulty", body)
        self.assertIn("Comments", body)
        self.assertIn("/planning/tasks/T01", body)
        self.assertIn("/planning/tasks/T02", body)
        self.assertNotIn("/planning/tasks/T03", body)
        self.assertIn("/threads/T01", body)
        self.assertIn("visible reply", body)
        self.assertIn('class="col-task-main"', body)
        self.assertIn('class="page-shell page-shell-wide"', body)
        self.assertIn('href="/planning/task-priorities/?view=done"', body)
        self.assertIn('href="/planning/task-priorities/?view=all"', body)
        self.assertNotIn("Future typed root", body)

    def test_done_task_view_shows_only_done_tasks(self) -> None:
        status, _, body = self.get("/planning/task-priorities/", "view=done")

        self.assertEqual(status, "200 OK")
        self.assertIn("Done task table", body)
        self.assertIn("/planning/tasks/T03", body)
        self.assertNotIn("/planning/tasks/T01", body)
        self.assertNotIn("/planning/tasks/T02", body)
        self.assertIn('class="thread-chip thread-chip-active"', body)

    def test_all_task_view_shows_open_and_done_tasks(self) -> None:
        status, _, body = self.get("/planning/task-priorities/", "view=all")

        self.assertEqual(status, "200 OK")
        self.assertIn("All task table", body)
        self.assertIn("/planning/tasks/T01", body)
        self.assertIn("/planning/tasks/T02", body)
        self.assertIn("/planning/tasks/T03", body)

    def test_task_detail_page_shows_task_thread_actions(self) -> None:
        status, headers, body = self.get("/planning/tasks/T01")

        self.assertEqual(status, "200 OK")
        self.assertEqual(headers["Content-Type"], "text/html; charset=utf-8")
        self.assertIn("First task thread", body)
        self.assertIn("/threads/T01", body)
        self.assertIn("/compose/reply?thread_id=T01&parent_id=T01", body)

    def test_task_detail_page_links_dependencies(self) -> None:
        status, _, body = self.get("/planning/tasks/T02")

        self.assertEqual(status, "200 OK")
        self.assertIn("/planning/tasks/T01", body)
        self.assertIn("Second task thread", body)

    def test_unknown_task_returns_404(self) -> None:
        status, _, body = self.get("/planning/tasks/T99")

        self.assertEqual(status, "404 Not Found")
        self.assertIn("could not be located", body)


if __name__ == "__main__":
    unittest.main()
