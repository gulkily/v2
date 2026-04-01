from __future__ import annotations

import json
import sqlite3
import subprocess
import tempfile
import unittest
from pathlib import Path
from textwrap import dedent

from forum_cgi.posting import commit_post
from forum_core.php_native_reads import (
    affected_thread_ids_for_touched_paths,
    board_index_snapshot_path,
    build_board_index_snapshot,
    build_profile_snapshot,
    build_thread_snapshot,
    rebuild_php_native_profile_snapshots,
    rebuild_php_native_thread_snapshots,
    thread_snapshot_db_path,
)
from forum_core.php_native_reads_db import load_php_native_snapshot


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

    def test_build_board_index_snapshot_uses_resolved_thread_title(self) -> None:
        self.write_record(
            "records/posts/root-201.txt",
            """
            Post-ID: root-201
            Board-Tags: general
            Subject: Original title

            Snapshot preview.
            """,
        )
        self.write_record(
            "records/thread-title-updates/thread-title-update-201.txt",
            """
            Record-ID: thread-title-update-201
            Thread-ID: root-201
            Timestamp: 2026-03-28T12:00:00Z

            Snapshot renamed
            """,
        )
        self.commit_paths("records/posts", "records/thread-title-updates", message="Seed renamed snapshot fixture")

        snapshot = build_board_index_snapshot(self.repo_root)

        self.assertEqual(snapshot["thread_rows"][0]["subject"], "Snapshot renamed")

    def test_build_thread_snapshot_includes_expected_thread_page_content(self) -> None:
        self.write_record(
            "records/posts/T01.txt",
            """
            Post-ID: T01
            Board-Tags: general planning
            Subject: Example task thread
            Thread-Type: task
            Task-Status: proposed
            Task-Presentability-Impact: 0.80
            Task-Implementation-Difficulty: 0.30
            Task-Depends-On: T00
            Task-Sources: todo.txt

            Ship a task thread through the normal discussion flow.
            """,
        )
        self.write_record(
            "records/posts/reply-001.txt",
            """
            Post-ID: reply-001
            Board-Tags: general
            Thread-ID: T01
            Parent-ID: T01

            First visible reply.
            """,
        )
        self.commit_paths("records/posts", message="Seed task thread fixture")

        snapshot = build_thread_snapshot("T01", self.repo_root)

        self.assertEqual(snapshot["route"], "/threads/T01")
        self.assertEqual(snapshot["title"], "Example task thread")
        self.assertEqual(snapshot["feed_href"], "/threads/T01?format=rss")
        self.assertIn("Task metadata", snapshot["content_html"])
        self.assertIn("compose a reply", snapshot["content_html"])
        self.assertIn("change title", snapshot["content_html"])
        self.assertIn("Replies", snapshot["content_html"])
        self.assertIn("First visible reply.", snapshot["content_html"])

    def test_build_profile_snapshot_includes_expected_profile_page_content(self) -> None:
        self.write_record(
            "records/posts/root-301.txt",
            """
            Post-ID: root-301
            Board-Tags: general
            Subject: Profile seed
            Signer-Fingerprint: ABCDEF0123456789ABCDEF0123456789ABCDEF01
            Identity-ID: openpgp:ABCDEF0123456789ABCDEF0123456789ABCDEF01

            Signed body.
            """,
        )
        self.write_record(
            "records/identity/identity-bootstrap-openpgp-ABCDEF0123456789ABCDEF0123456789ABCDEF01.txt",
            """
            Post-ID: identity-bootstrap-openpgp-ABCDEF0123456789ABCDEF0123456789ABCDEF01
            Identity-ID: openpgp:ABCDEF0123456789ABCDEF0123456789ABCDEF01
            Signer-Fingerprint: ABCDEF0123456789ABCDEF0123456789ABCDEF01
            Bootstrap-By-Post: root-301
            Bootstrap-By-Thread: root-301

            -----BEGIN PGP PUBLIC KEY BLOCK-----
            Example key
            -----END PGP PUBLIC KEY BLOCK-----
            """,
        )
        self.commit_paths("records/posts", "records/identity", message="Seed profile snapshot fixture")

        snapshot = build_profile_snapshot("openpgp:ABCDEF0123456789ABCDEF0123456789ABCDEF01", self.repo_root)

        self.assertEqual(snapshot["route"], "/profiles/openpgp-ABCDEF0123456789ABCDEF0123456789ABCDEF01")
        self.assertIn("Public profile for", snapshot["content_html"])
        self.assertIn("root-301", snapshot["content_html"])
        self.assertIn("visible posts", snapshot["content_html"])

    def test_rebuild_php_native_profile_snapshots_backfills_sqlite_rows(self) -> None:
        self.write_record(
            "records/posts/root-302.txt",
            """
            Post-ID: root-302
            Board-Tags: general
            Subject: Profile target
            Signer-Fingerprint: ABCDEF0123456789ABCDEF0123456789ABCDEF02
            Identity-ID: openpgp:ABCDEF0123456789ABCDEF0123456789ABCDEF02

            Snapshot me.
            """,
        )
        self.write_record(
            "records/identity/identity-bootstrap-openpgp-ABCDEF0123456789ABCDEF0123456789ABCDEF02.txt",
            """
            Post-ID: identity-bootstrap-openpgp-ABCDEF0123456789ABCDEF0123456789ABCDEF02
            Identity-ID: openpgp:ABCDEF0123456789ABCDEF0123456789ABCDEF02
            Signer-Fingerprint: ABCDEF0123456789ABCDEF0123456789ABCDEF02
            Bootstrap-By-Post: root-302
            Bootstrap-By-Thread: root-302

            -----BEGIN PGP PUBLIC KEY BLOCK-----
            Example key
            -----END PGP PUBLIC KEY BLOCK-----
            """,
        )
        self.commit_paths("records/posts", "records/identity", message="Seed profile backfill fixture")

        rebuilt = rebuild_php_native_profile_snapshots(self.repo_root)

        self.assertEqual(rebuilt, ["openpgp:ABCDEF0123456789ABCDEF0123456789ABCDEF02"])
        connection = sqlite3.connect(thread_snapshot_db_path(self.repo_root))
        try:
            snapshot = load_php_native_snapshot(connection, "profile/openpgp-ABCDEF0123456789ABCDEF0123456789ABCDEF02")
        finally:
            connection.close()
        assert snapshot is not None
        self.assertEqual(snapshot["route"], "/profiles/openpgp-ABCDEF0123456789ABCDEF0123456789ABCDEF02")
        self.assertIn("Public profile for", snapshot["content_html"])
        self.assertIn("root-302", snapshot["content_html"])

    def test_affected_thread_ids_for_post_moderation_and_title_updates(self) -> None:
        self.write_record(
            "records/posts/root-001.txt",
            """
            Post-ID: root-001
            Board-Tags: general
            Subject: Root thread

            Root body.
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
            "records/moderation/hide-reply-001.txt",
            """
            Record-ID: hide-reply-001
            Action: hide
            Target-Type: post
            Target-ID: reply-001
            Timestamp: 2026-03-25T12:00:00Z

            Hidden reply.
            """,
        )
        self.write_record(
            "records/thread-title-updates/thread-title-update-001.txt",
            """
            Record-ID: thread-title-update-001
            Thread-ID: root-001
            Timestamp: 2026-03-28T12:00:00Z

            Renamed thread
            """,
        )
        self.commit_paths("records/posts", "records/moderation", "records/thread-title-updates", message="Seed invalidation fixture")

        affected = affected_thread_ids_for_touched_paths(
            self.repo_root,
            (
                "records/posts/reply-001.txt",
                "records/moderation/hide-reply-001.txt",
                "records/thread-title-updates/thread-title-update-001.txt",
            ),
        )

        self.assertEqual(affected, ["root-001"])

    def test_rebuild_php_native_thread_snapshots_backfills_sqlite_rows(self) -> None:
        self.write_record(
            "records/posts/root-101.txt",
            """
            Post-ID: root-101
            Board-Tags: general
            Subject: Snapshot target

            Snapshot me.
            """,
        )
        self.commit_paths("records/posts", message="Seed backfill fixture")

        rebuilt = rebuild_php_native_thread_snapshots(self.repo_root)

        self.assertEqual(rebuilt, ["root-101"])
        connection = sqlite3.connect(thread_snapshot_db_path(self.repo_root))
        try:
            snapshot = load_php_native_snapshot(connection, "thread/root-101")
        finally:
            connection.close()
        assert snapshot is not None
        self.assertEqual(snapshot["route"], "/threads/root-101")
        self.assertIn("Snapshot target", snapshot["content_html"])


if __name__ == "__main__":
    unittest.main()
