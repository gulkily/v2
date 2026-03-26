from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from textwrap import dedent

from forum_cgi.posting import commit_post
from forum_core.php_native_reads import board_index_snapshot_path, build_board_index_snapshot


class PhpNativeReadSnapshotTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.tempdir.name)
        self.run_git("init")
        self.run_git("config", "user.name", "Test User")
        self.run_git("config", "user.email", "test@example.com")

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def run_git(self, *args: str) -> str:
        result = subprocess.run(
            ["git", "-C", str(self.repo_root), *args],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return result.stdout.strip()

    def write_record(self, relative_path: str, raw_text: str) -> Path:
        path = self.repo_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(dedent(raw_text).lstrip(), encoding="ascii")
        return path

    def commit_paths(self, *relative_paths: str, message: str) -> None:
        self.run_git("add", *relative_paths)
        self.run_git("commit", "-m", message)

    def test_build_board_index_snapshot_matches_v1_contract_shape(self) -> None:
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
            "records/moderation/hide-root-001.txt",
            """
            Record-ID: hide-root-001
            Action: hide
            Target-Type: thread
            Target-ID: root-001
            Timestamp: 2026-03-25T12:00:00Z

            Hidden from index.
            """,
        )
        self.commit_paths("records/posts", "records/moderation", message="Seed snapshot fixture")

        snapshot = build_board_index_snapshot(self.repo_root)

        self.assertEqual(snapshot["route"], "/")
        self.assertEqual(
            snapshot["stats"],
            {
                "post_count": 3,
                "thread_count": 1,
                "board_tag_count": 1,
            },
        )
        self.assertEqual(
            snapshot["thread_rows"],
            [
                {
                    "post_id": "root-002",
                    "thread_href": "/threads/root-002",
                    "subject": "Planning thread",
                    "preview": "Planning preview.",
                    "tags": ["planning"],
                    "reply_count": 0,
                    "thread_type": "task",
                }
            ],
        )

    def test_commit_post_refreshes_board_index_snapshot(self) -> None:
        post_path = self.write_record(
            "records/posts/root-101.txt",
            """
            Post-ID: root-101
            Board-Tags: general updates
            Subject: Fresh thread

            Fresh preview.
            """,
        )

        commit_post(self.repo_root, [post_path], message="Add root-101")

        snapshot_path = board_index_snapshot_path(self.repo_root)
        self.assertTrue(snapshot_path.exists())
        snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
        self.assertEqual(snapshot["route"], "/")
        self.assertEqual(snapshot["stats"]["post_count"], 1)
        self.assertEqual(snapshot["stats"]["thread_count"], 1)
        self.assertEqual(snapshot["stats"]["board_tag_count"], 2)
        self.assertEqual(
            snapshot["thread_rows"],
            [
                {
                    "post_id": "root-101",
                    "thread_href": "/threads/root-101",
                    "subject": "Fresh thread",
                    "preview": "Fresh preview.",
                    "tags": ["updates"],
                    "reply_count": 0,
                    "thread_type": None,
                }
            ],
        )


if __name__ == "__main__":
    unittest.main()
