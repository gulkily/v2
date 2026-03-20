from __future__ import annotations

import os
import sqlite3
import subprocess
import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from textwrap import dedent
from unittest import mock

from forum_core.operation_events import operation_events_path, start_operation, complete_operation
from forum_web.web import application


class InstanceInfoPageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.tempdir.name)
        self.write_record(
            "records/posts/root-001.txt",
            """
            Post-ID: root-001
            Board-Tags: general
            Subject: Hello

            Body.
            """,
        )
        self.write_record(
            "records/instance/public.txt",
            """
            Instance-Name: Demo instance
            Admin-Name: Demo operator
            Admin-Contact: operator@example.invalid
            Retention-Policy: Keep canonical records in git.
            Install-Date: 2026-03-15

            Demo instance summary.
            """,
        )
        subprocess.run(["git", "init"], cwd=self.repo_root, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=self.repo_root, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=self.repo_root, check=True)
        subprocess.run(["git", "add", "."], cwd=self.repo_root, check=True)
        subprocess.run(["git", "commit", "-m", "initial"], cwd=self.repo_root, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def write_record(self, relative_path: str, raw_text: str) -> None:
        path = self.repo_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(dedent(raw_text).lstrip(), encoding="utf-8")

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

        with mock.patch.dict(os.environ, {"FORUM_REPO_ROOT": str(self.repo_root)}, clear=False):
            body = b"".join(application(environ, start_response)).decode("utf-8")

        return response["status"], dict(response["headers"]), body

    def test_board_index_links_to_project_information_page(self) -> None:
        status, _, body = self.get("/")

        self.assertEqual(status, "200 OK")
        self.assertIn('/instance/', body)
        self.assertIn(">Project info</a>", body)

    def test_instance_info_page_renders_public_facts(self) -> None:
        status, headers, body = self.get("/instance/")

        self.assertEqual(status, "200 OK")
        self.assertEqual(headers["Content-Type"], "text/html; charset=utf-8")
        self.assertIn("Project information", body)
        self.assertIn("Project overview", body)
        self.assertIn("Demo instance", body)
        self.assertIn("Demo operator", body)
        self.assertIn("operator@example.invalid", body)
        self.assertIn("Keep canonical records in git.", body)
        self.assertIn("2026-03-15", body)
        self.assertIn("records/instance/public.txt", body)
        self.assertIn("current commit", body)
        self.assertIn("Project FAQ", body)
        self.assertIn("Why are posts ASCII-only?", body)
        self.assertIn("generic social feed", body)

    def test_instance_info_page_marks_missing_values(self) -> None:
        (self.repo_root / "records" / "instance" / "public.txt").unlink()

        status, _, body = self.get("/instance/")

        self.assertEqual(status, "200 OK")
        self.assertIn("Not published.", body)
        self.assertIn("records/instance/public.txt", body)
        self.assertIn("Project information", body)

    def test_instance_info_page_renders_recent_operations_panel(self) -> None:
        slow_handle = start_operation(
            self.repo_root,
            operation_kind="request",
            operation_name="GET /activity/",
            metadata={"method": "GET", "path": "/activity/", "view": "code"},
        )
        complete_operation(slow_handle)
        connection = sqlite3.connect(operation_events_path(self.repo_root))
        try:
            connection.execute(
                "UPDATE operation_events SET total_duration_ms = ?, started_at = ?, updated_at = ?, ended_at = ? WHERE operation_id = ?",
                (2500.0, "2026-03-20T02:00:00Z", "2026-03-20T02:00:01Z", "2026-03-20T02:00:02Z", slow_handle.operation_id),
            )
            connection.commit()
        finally:
            connection.close()

        status, _, body = self.get("/instance/")

        self.assertEqual(status, "200 OK")
        self.assertIn("Recent slow operations", body)
        self.assertIn("GET /activity/", body)
        self.assertIn("method: GET", body)
        self.assertIn("path: /activity/", body)
        self.assertIn("view: code", body)


if __name__ == "__main__":
    unittest.main()
