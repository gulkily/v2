from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from textwrap import dedent
from unittest import mock

from forum_web.web import application


class TaskThreadPagesTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.tempdir.name)
        self.run_command(["git", "init"], cwd=self.repo_root)
        self.run_command(["git", "config", "user.name", "Codex Test"], cwd=self.repo_root)
        self.run_command(["git", "config", "user.email", "codex@example.com"], cwd=self.repo_root)
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

    def run_command(self, command: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            command,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )

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

    def post(self, path: str) -> tuple[str, dict[str, str], str]:
        environ = {
            "PATH_INFO": path,
            "QUERY_STRING": "",
            "REQUEST_METHOD": "POST",
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
        self.assertIn('id="draft-status"', body)
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

    def test_task_detail_page_shows_mark_done_action(self) -> None:
        status, _, body = self.get("/planning/tasks/T01")

        self.assertEqual(status, "200 OK")
        self.assertIn('class="site-header site-header--page"', body)
        self.assertIn("Task actions", body)
        self.assertIn("/planning/tasks/T01/mark-done", body)
        self.assertIn("mark task done", body)

    def test_mark_done_updates_task_status_and_returns_task_page(self) -> None:
        status, _, body = self.post("/planning/tasks/T01/mark-done")

        self.assertEqual(status, "200 OK")
        self.assertIn("Task updated", body)
        self.assertIn("Status changed from proposed to done.", body)
        self.assertIn("<strong>Status:</strong> done", body)
        self.assertIn('/planning/task-priorities/?view=done', body)
        record_text = (self.repo_root / "records/posts/T01.txt").read_text(encoding="ascii")
        self.assertIn("Task-Status: done", record_text)

    def test_mark_done_rejects_already_done_task(self) -> None:
        self.post("/planning/tasks/T01/mark-done")

        status, _, body = self.post("/planning/tasks/T01/mark-done")

        self.assertEqual(status, "409 Conflict")
        self.assertIn("Task update failed", body)
        self.assertIn("task is already done: T01", body)

    def test_done_task_moves_between_filtered_priority_views(self) -> None:
        self.post("/planning/tasks/T01/mark-done")

        _, _, open_body = self.get("/planning/task-priorities/")
        _, _, done_body = self.get("/planning/task-priorities/", "view=done")
        _, _, all_body = self.get("/planning/task-priorities/", "view=all")
        _, _, detail_body = self.get("/planning/tasks/T01")

        self.assertNotIn("/planning/tasks/T01", open_body)
        self.assertIn("/planning/tasks/T01", done_body)
        self.assertIn("/planning/tasks/T01", all_body)
        self.assertIn("This task is already marked done.", detail_body)
        self.assertNotIn("/planning/tasks/T01/mark-done", detail_body)


if __name__ == "__main__":
    unittest.main()
