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
        self.write_record(
            "records/posts/root-003.txt",
            """
            Post-ID: root-003
            Board-Tags: general
            Subject: Same words

            Same words
            """,
        )

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def write_record(self, relative_path: str, raw_text: str) -> None:
        path = self.repo_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(dedent(raw_text).lstrip(), encoding="ascii")

    def run_git(self, *args: str, env: dict[str, str] | None = None) -> str:
        result = subprocess.run(
            ["git", "-C", str(self.repo_root), *args],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )
        return result.stdout.strip()

    def init_git_repo(self) -> None:
        self.run_git("init")
        self.run_git("config", "user.name", "Test User")
        self.run_git("config", "user.email", "test@example.com")

    def commit_posts(self, message: str, timestamp: str) -> None:
        env = {
            "PATH": os.environ["PATH"],
            "GIT_AUTHOR_DATE": timestamp,
            "GIT_COMMITTER_DATE": timestamp,
        }
        self.run_git("add", "records/posts", env=env)
        self.run_git("commit", "-m", message, env=env)

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

    def test_board_index_uses_shared_page_shell(self) -> None:
        status, headers, body = self.get("/")

        self.assertEqual(status, "200 OK")
        self.assertEqual(headers["Content-Type"], "text/html; charset=utf-8")
        self.assertIn('class="site-header site-header--page"', body)
        self.assertIn('class="site-footer"', body)
        self.assertNotIn("Board Index", body)
        self.assertNotIn("Threads worth opening", body)
        self.assertNotIn(">Visible threads<", body)
        self.assertIn("/threads/root-001", body)
        self.assertIn("Hello world", body)
        self.assertIn("First line preview.", body)
        self.assertIn("posts loaded", body)
        self.assertIn("board tags", body)
        self.assertTrue(body.index("/threads/root-001") < body.index("posts loaded"))
        self.assertNotIn('class="front-header"', body)
        self.assertNotIn('class="front-layout"', body)
        self.assertNotIn("Kindness first.", body)

    def test_board_index_kindness_header_flag_defaults_off_and_can_be_enabled(self) -> None:
        _, _, default_body = self.get("/")

        self.assertNotIn('class="site-header-band"', default_body)
        self.assertNotIn("Kindness first.", default_body)

        with mock.patch.dict(
            os.environ,
            {
                "FORUM_REPO_ROOT": str(self.repo_root),
                "FORUM_ENABLE_KINDNESS_HEADER": "1",
            },
            clear=False,
        ):
            environ = {
                "PATH_INFO": "/",
                "QUERY_STRING": "",
                "REQUEST_METHOD": "GET",
                "CONTENT_LENGTH": "0",
                "wsgi.input": BytesIO(b""),
            }
            response: dict[str, object] = {}

            def start_response(status: str, headers: list[tuple[str, str]]) -> None:
                response["status"] = status
                response["headers"] = headers

            enabled_body = b"".join(application(environ, start_response)).decode("utf-8")

        self.assertEqual(response["status"], "200 OK")
        self.assertIn('class="site-header-band"', enabled_body)
        self.assertIn("Kindness first.", enabled_body)

    def test_board_index_preserves_key_destination_links(self) -> None:
        status, _, body = self.get("/")

        self.assertEqual(status, "200 OK")
        self.assertIn('/compose/thread', body)
        self.assertIn('/instance/', body)
        self.assertIn('/activity/', body)
        self.assertIn('data-profile-nav-link', body)
        self.assertIn('data-profile-nav-state="unresolved"', body)
        self.assertIn('aria-disabled="true"', body)
        self.assertIn('tabindex="-1"', body)
        self.assertIn('>My profile</a>', body)
        self.assertIn('/assets/profile_nav.js', body)
        self.assertIn('data-username-claim-cta', body)
        self.assertIn('/assets/username_claim_cta.js', body)
        self.assertIn('Choose your username', body)
        self.assertIn('>Project info</a>', body)
        self.assertIn('>Activity</a>', body)
        self.assertNotIn('view repository history', body)
        self.assertNotIn('/activity/?view=moderation', body)
        self.assertNotIn('moderation activity', body)
        self.assertNotIn('/planning/task-priorities/', body)

    def test_board_index_suppresses_default_listing_metadata(self) -> None:
        status, _, body = self.get("/")

        self.assertEqual(status, "200 OK")
        self.assertNotIn(">root-001<", body)
        self.assertNotIn(">root-002<", body)
        self.assertNotIn(">root-003<", body)
        self.assertIn("[general] [meta]", body)
        self.assertNotIn(">Same words</a></h3><p class=\"board-index-thread-tags\">[general]</p>", body)
        self.assertNotIn(">Same words</a></h3><p>Same words</p>", body)
        self.assertNotIn("0 replies", body)
        self.assertIn("1 reply", body)

    def test_board_index_orders_threads_by_commit_recency_when_index_is_available(self) -> None:
        self.init_git_repo()
        self.commit_posts("Add roots", "2026-03-17T09:00:00+00:00")

        self.write_record(
            "records/posts/root-001.txt",
            """
            Post-ID: root-001
            Board-Tags: general meta
            Subject: Hello world

            Freshly updated body.
            """,
        )
        self.commit_posts("Update root-001", "2026-03-17T12:00:00+00:00")

        status, _, body = self.get("/")

        self.assertEqual(status, "200 OK")
        self.assertTrue(body.index("/threads/root-001") < body.index("/threads/root-002"))


if __name__ == "__main__":
    unittest.main()
