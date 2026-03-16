from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from textwrap import dedent
from unittest import mock

from forum_web.repository import load_posts
from forum_web.web import build_posts_index, fetch_recent_commits, resolve_commit_posts


class SiteActivityGitLogHelpersTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.tempdir.name)
        self.run_git("init")
        self.run_git("config", "user.name", "Test User")
        self.run_git("config", "user.email", "test@example.com")

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def run_git(self, *args: str) -> None:
        subprocess.run(["git", "-C", str(self.repo_root), *args], check=True)

    def write_record(self, relative_path: str, content: str) -> Path:
        path = self.repo_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(dedent(content).lstrip(), encoding="ascii")
        return path

    def commit(self, message: str) -> str:
        self.run_git("add", "records/posts")
        subprocess.run(
            ["git", "-C", str(self.repo_root), "commit", "-m", message],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        result = subprocess.run(
            ["git", "-C", str(self.repo_root), "rev-parse", "HEAD"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return result.stdout.strip()

    def test_fetch_recent_commits_returns_commits_with_files(self) -> None:
        self.write_record(
            "records/posts/root-001.txt",
            """
            Post-ID: root-001
            Board-Tags: general

            Body one.
            """,
        )
        first_commit = self.commit("Add root-001")

        self.write_record(
            "records/posts/reply-002.txt",
            """
            Post-ID: reply-002
            Board-Tags: general
            Thread-ID: root-001
            Parent-ID: root-001

            Reply body.
            """,
        )
        second_commit = self.commit("Add reply-002")

        commits = fetch_recent_commits(self.repo_root, limit=2)
        self.assertEqual(len(commits), 2)
        self.assertEqual(commits[0].commit_id, second_commit)
        self.assertEqual(commits[1].commit_id, first_commit)
        self.assertIn("records/posts/reply-002.txt", commits[0].files)

    def test_resolve_commit_posts_maps_to_post_objects(self) -> None:
        self.write_record(
            "records/posts/root-010.txt",
            """
            Post-ID: root-010
            Board-Tags: general

            Root body.
            """,
        )
        self.commit("Add root-010")
        posts = load_posts(self.repo_root / "records" / "posts")
        posts_index = build_posts_index(posts, self.repo_root)

        commits = fetch_recent_commits(self.repo_root, limit=1)
        self.assertEqual(len(commits), 1)
        resolved = resolve_commit_posts(commits[0], posts_index)
        self.assertEqual(len(resolved), 1)
        self.assertEqual(resolved[0].post_id, "root-010")


if __name__ == "__main__":
    unittest.main()
