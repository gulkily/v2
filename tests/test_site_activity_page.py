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
        self.init_git_repo()
        self.commit_record("records/posts/root-010.txt", "Add root")
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
        self.commit_record("records/posts/reply-020.txt", "Add reply")
        self.write_record(
            "records/moderation/pin-root-010.txt",
            """
            Record-ID: pin-root-010
            Action: pin
            Target-Type: thread
            Target-ID: root-010
            Timestamp: 2026-03-17T23:00:00Z

            Pinning the thread.
            """,
        )
        self.commit_record("records/moderation/pin-root-010.txt", "Pin root")

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def write_record(self, relative_path: str, raw_text: str) -> None:
        path = self.repo_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(dedent(raw_text).lstrip(), encoding="ascii")

    def run_git(self, *args: str) -> None:
        subprocess.run(["git", "-C", str(self.repo_root), *args], check=True)

    def init_git_repo(self) -> None:
        self.run_git("init")
        self.run_git("config", "user.name", "Test User")
        self.run_git("config", "user.email", "test@example.com")

    def commit_record(self, relative_path: str, message: str) -> None:
        self.run_git("add", relative_path)
        self.run_git("commit", "-m", message)

    def latest_commit_short(self) -> str:
        result = subprocess.run(
            ["git", "-C", str(self.repo_root), "log", "-1", "--format=%H"],
            check=True,
            stdout=subprocess.PIPE,
            text=True,
        )
        return result.stdout.strip()[:7]

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

    def test_activity_page_renders_records_and_metadata(self) -> None:
        status, headers, body = self.get("/activity/")

        self.assertEqual(status, "200 OK")
        self.assertEqual(headers["Content-Type"], "text/html; charset=utf-8")
        self.assertIn('class="site-header site-header--page"', body)
        self.assertIn('class="site-footer"', body)
        self.assertNotIn('class="front-layout"', body)
        self.assertIn("Canonical activity stream", body)
        self.assertIn("all activity", body)
        self.assertIn("content activity", body)
        self.assertIn("moderation activity", body)
        self.assertIn('class="post-card"', body)
        self.assertIn("First root", body)
        self.assertIn("root-010", body)
        self.assertIn("reply-020", body)
        self.assertIn("pin thread", body)
        self.assertIn("Add reply", body)
        self.assertIn("Add root", body)
        self.assertTrue(body.index("pin thread") < body.index("Add reply"))
        self.assertTrue(body.index("Add reply") < body.index("Add root"))
        self.assertIn(self.latest_commit_short(), body)
        self.assertIn("Working tree", body)
        self.assertIn("records/instance/public.txt", body)

    def test_activity_page_filters_content_and_moderation(self) -> None:
        _, _, content_body = self.get("/activity/", "view=content")
        _, _, moderation_body = self.get("/activity/", "view=moderation")

        self.assertIn("Add reply", content_body)
        self.assertNotIn("pin thread", content_body)
        self.assertIn("pin thread", moderation_body)
        self.assertNotIn("Add reply", moderation_body)


if __name__ == "__main__":
    unittest.main()
