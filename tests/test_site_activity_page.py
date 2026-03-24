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
        self.write_record("forum_web_stub.py", "print('helper')\n")
        self.write_record("docs/notes.md", "# Activity notes\n")
        self.commit_paths(["forum_web_stub.py", "docs/notes.md"], "Add ui helper")

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
        self.run_git("remote", "add", "origin", "https://github.com/example/forum.git")

    def commit_record(self, relative_path: str, message: str) -> None:
        self.run_git("add", relative_path)
        self.run_git("commit", "-m", message)

    def commit_paths(self, relative_paths: list[str], message: str) -> None:
        self.run_git("add", *relative_paths)
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
        self.assertNotIn("Activity feed", body)
        self.assertNotIn("Repository history", body)
        self.assertNotIn("Browse only git-backed content activity for this instance.", body)
        self.assertIn("all activity", body)
        self.assertIn("content activity", body)
        self.assertIn("moderation activity", body)
        self.assertIn("code activity", body)
        self.assertIn('rel="alternate" type="application/rss+xml"', body)
        self.assertIn('href="/activity/?view=content&amp;format=rss"', body)
        self.assertIn(">RSS feed</a>", body)
        self.assertIn('class="post-card"', body)
        self.assertIn("First root", body)
        self.assertIn("root-010", body)
        self.assertIn("reply-020", body)
        self.assertIn("Test User &lt;test@example.com&gt;", body)
        self.assertIn("view on GitHub", body)
        self.assertIn("https://github.com/example/forum/commit/", body)
        self.assertIn("Add reply", body)
        self.assertIn("Add root", body)
        self.assertTrue(body.index("Add reply") < body.index("Add root"))
        self.assertNotIn(self.latest_commit_short(), body)
        self.assertNotIn("Repository snapshot", body)
        self.assertNotIn("Working tree", body)
        self.assertNotIn("records/instance/public.txt", body)
        self.assertNotIn("pin thread", body)
        self.assertNotIn("Add ui helper", body)
        self.assertNotIn("One filtered timeline for repository content, moderation, and code activity on this instance.", body)

    def test_activity_page_filters_content_moderation_and_code(self) -> None:
        _, _, all_body = self.get("/activity/", "view=all")
        _, _, default_body = self.get("/activity/")
        _, _, content_body = self.get("/activity/", "view=content")
        _, _, moderation_body = self.get("/activity/", "view=moderation")
        _, _, code_body = self.get("/activity/", "view=code")

        self.assertIn("Add reply", all_body)
        self.assertIn("pin thread", all_body)
        self.assertIn("Add ui helper", all_body)
        self.assertIn("Add reply", default_body)
        self.assertNotIn("pin thread", default_body)
        self.assertNotIn("Add ui helper", default_body)
        self.assertIn("Add reply", content_body)
        self.assertIn("Content commit", content_body)
        self.assertNotIn("pin thread", content_body)
        self.assertNotIn("Add ui helper", content_body)
        self.assertIn("pin thread", moderation_body)
        self.assertNotIn("Add reply", moderation_body)
        self.assertNotIn("Add ui helper", moderation_body)
        self.assertIn("Add ui helper", code_body)
        self.assertIn("Code commit", code_body)
        self.assertIn("docs/notes.md", code_body)
        self.assertIn("view on GitHub", code_body)
        self.assertNotIn("pin thread", code_body)
        self.assertNotIn("Add reply", code_body)
        self.assertIn('href="/activity/?view=all"', default_body)

    def test_moderation_route_redirects_to_filtered_activity_view(self) -> None:
        status, headers, body = self.get("/moderation/")

        self.assertEqual(status, "302 Found")
        self.assertEqual(headers["Location"], "/activity/?view=moderation")
        self.assertEqual(body, "")

    def test_activity_page_renders_pagination_links_per_view(self) -> None:
        for index in range(15):
            self.write_record(
                f"records/posts/root-{index + 100}.txt",
                f"""
                Post-ID: root-{index + 100}
                Board-Tags: general
                Subject: Root {index + 100}

                Body {index + 100}.
                """,
            )
            self.commit_record(f"records/posts/root-{index + 100}.txt", f"Add root {index + 100}")

        _, _, page_one = self.get("/activity/", "view=content")
        _, _, page_two = self.get("/activity/", "view=content&page=2")

        self.assertIn('href="/activity/?view=content&page=2"', page_one)
        self.assertIn("older activity", page_one)
        self.assertNotIn("newer activity", page_one)
        self.assertIn('href="/activity/?view=content&page=1"', page_two)
        self.assertIn("newer activity", page_two)
        self.assertIn("Add root 114", page_one)
        self.assertNotIn("Add root 102", page_one)
        self.assertIn("Add root 102", page_two)

    def test_activity_route_can_render_rss_feed(self) -> None:
        status, headers, body = self.get("/activity/", "view=all&format=rss")

        self.assertEqual(status, "200 OK")
        self.assertEqual(headers["Content-Type"], "application/rss+xml; charset=utf-8")
        self.assertIn('<?xml version="1.0" encoding="UTF-8"?>', body)
        self.assertIn("activity (all)</title>", body)
        self.assertIn("<link>/activity/?view=all</link>", body)
        self.assertIn("<guid>commit:", body)
        self.assertIn("<guid>moderation:", body)
        self.assertIn("Add ui helper", body)
        self.assertIn("Pinning the thread.", body)


if __name__ == "__main__":
    unittest.main()
