from __future__ import annotations

import os
import sqlite3
import subprocess
import tempfile
import unittest
from types import SimpleNamespace
from pathlib import Path
from textwrap import dedent
from unittest import mock

from forum_core.post_index import (
    IndexedAuthorRow,
    POST_INDEX_SCHEMA_VERSION,
    author_id_for_post,
    author_row_for_post,
    current_post_index_schema_version,
    open_post_index,
    post_index_path,
    rebuild_post_index,
)
from forum_core.identity import build_identity_id
from forum_cgi.posting import store_post
from forum_cgi.task_status import submit_mark_task_done
from forum_web.profiles import IdentityContext
from forum_web.repository import load_posts, parse_post_text


class PostIndexSchemaTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.tempdir.name)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_open_post_index_creates_expected_schema_path(self) -> None:
        index = open_post_index(self.repo_root)
        try:
            self.assertEqual(index.path, post_index_path(self.repo_root))
            self.assertTrue(index.path.exists())
            self.assertEqual(current_post_index_schema_version(index.connection), POST_INDEX_SCHEMA_VERSION)
        finally:
            index.connection.close()

    def test_open_post_index_is_idempotent(self) -> None:
        first = open_post_index(self.repo_root)
        first.connection.execute(
            "INSERT INTO posts (post_id, relative_path, subject, thread_id, parent_id, root_thread_id, body, is_root) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            ("root-001", "records/posts/root-001.txt", "Hello", None, None, "root-001", "body", 1),
        )
        first.connection.commit()
        first.connection.close()

        second = open_post_index(self.repo_root)
        try:
            row = second.connection.execute(
                "SELECT post_id, relative_path FROM posts WHERE post_id = ?",
                ("root-001",),
            ).fetchone()
            self.assertIsNotNone(row)
            assert row is not None
            self.assertEqual(row["relative_path"], "records/posts/root-001.txt")
            self.assertEqual(current_post_index_schema_version(second.connection), POST_INDEX_SCHEMA_VERSION)
        finally:
            second.connection.close()

    def test_existing_database_upgrades_user_version_idempotently(self) -> None:
        db_path = post_index_path(self.repo_root)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(db_path)
        connection.execute("CREATE TABLE posts (post_id TEXT PRIMARY KEY, relative_path TEXT NOT NULL UNIQUE, subject TEXT NOT NULL, thread_id TEXT, parent_id TEXT, root_thread_id TEXT NOT NULL, body TEXT NOT NULL, is_root INTEGER NOT NULL)")
        connection.execute("PRAGMA user_version = 0")
        connection.commit()
        connection.close()

        index = open_post_index(self.repo_root)
        try:
            self.assertEqual(current_post_index_schema_version(index.connection), POST_INDEX_SCHEMA_VERSION)
        finally:
            index.connection.close()

    def test_existing_database_adds_author_schema_idempotently(self) -> None:
        db_path = post_index_path(self.repo_root)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(db_path)
        connection.execute(
            "CREATE TABLE posts (post_id TEXT PRIMARY KEY, relative_path TEXT NOT NULL UNIQUE, subject TEXT NOT NULL, thread_id TEXT, parent_id TEXT, root_thread_id TEXT NOT NULL, body TEXT NOT NULL, is_root INTEGER NOT NULL)"
        )
        connection.execute("PRAGMA user_version = 1")
        connection.commit()
        connection.close()

        index = open_post_index(self.repo_root)
        try:
            post_columns = {
                row["name"]
                for row in index.connection.execute("PRAGMA table_info(posts)")
            }
            author_tables = index.connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'authors'"
            ).fetchone()
            self.assertIn("author_id", post_columns)
            self.assertIsNotNone(author_tables)
            self.assertEqual(current_post_index_schema_version(index.connection), POST_INDEX_SCHEMA_VERSION)
        finally:
            index.connection.close()


class PostIndexAuthorHelpersTests(unittest.TestCase):
    def test_author_id_for_post_prefers_canonical_identity(self) -> None:
        post = parse_post_text(
            dedent(
                """
                Post-ID: root-001
                Board-Tags: general
                Subject: Hello

                Body.
                """
            ).lstrip()
        )
        post = post.__class__(
            **{
                **post.__dict__,
                "identity_id": build_identity_id("ABCDEF0123456789ABCDEF0123456789ABCDEF01"),
                "signer_fingerprint": "ABCDEF0123456789ABCDEF0123456789ABCDEF01",
            }
        )
        identity_context = IdentityContext(
            bootstraps_by_identity_id={},
            resolution=SimpleNamespace(
                canonical_identity_id=lambda identity_id: "openpgp:canonical",
                member_identity_ids=lambda identity_id: ("openpgp:canonical",),
            ),
            profile_update_records=(),
        )

        self.assertEqual(author_id_for_post(post, identity_context), "openpgp:canonical")

    def test_author_row_for_post_falls_back_to_fingerprint_label(self) -> None:
        post = parse_post_text(
            dedent(
                """
                Post-ID: root-001
                Board-Tags: general
                Subject: Hello

                Body.
                """
            ).lstrip()
        )
        post = post.__class__(
            **{
                **post.__dict__,
                "signer_fingerprint": "ABCDEF0123456789ABCDEF0123456789ABCDEF01",
            }
        )

        row = author_row_for_post(post, identity_context=None)

        self.assertEqual(
            row,
            IndexedAuthorRow(
                author_id="fingerprint:abcdef0123456789abcdef0123456789abcdef01",
                canonical_identity_id=None,
                display_name="ABCDEF0123456789..",
                display_name_source="fingerprint_fallback",
                signer_fingerprint="ABCDEF0123456789ABCDEF0123456789ABCDEF01",
            ),
        )

class PostIndexBuildTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.tempdir.name)
        (self.repo_root / "records" / "posts").mkdir(parents=True, exist_ok=True)
        self.run_git("init")
        self.run_git("config", "user.name", "Codex Test")
        self.run_git("config", "user.email", "codex@example.com")

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def run_git(self, *args: str, env: dict[str, str] | None = None) -> str:
        merged_env = None
        if env is not None:
            merged_env = dict(env)
        result = subprocess.run(
            ["git", "-C", str(self.repo_root), *args],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=merged_env,
        )
        return result.stdout.strip()

    def write_post(self, relative_path: str, raw_text: str) -> None:
        path = self.repo_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(dedent(raw_text).lstrip(), encoding="ascii")

    def commit_all(self, message: str, timestamp: str) -> None:
        env = {
            "GIT_AUTHOR_DATE": timestamp,
            "GIT_COMMITTER_DATE": timestamp,
            "PATH": os.environ["PATH"],
        }
        self.run_git("add", "records/posts", env=env)
        self.run_git("commit", "-m", message, env=env)

    def test_rebuild_post_index_stores_commit_derived_timestamps(self) -> None:
        self.write_post(
            "records/posts/root-001.txt",
            """
            Post-ID: root-001
            Board-Tags: general
            Subject: First root

            First body.
            """,
        )
        self.commit_all("Add root", "2026-03-17T10:00:00+00:00")

        self.write_post(
            "records/posts/root-001.txt",
            """
            Post-ID: root-001
            Board-Tags: general
            Subject: First root

            Updated body.
            """,
        )
        self.commit_all("Update root", "2026-03-17T12:00:00+00:00")

        rebuild_post_index(self.repo_root)
        index = open_post_index(self.repo_root)
        try:
            row = index.connection.execute(
                "SELECT created_at, updated_at, body FROM posts WHERE post_id = ?",
                ("root-001",),
            ).fetchone()
            self.assertIsNotNone(row)
            assert row is not None
            self.assertEqual(row["created_at"], "2026-03-17T10:00:00+00:00")
            self.assertEqual(row["updated_at"], "2026-03-17T12:00:00+00:00")
            self.assertEqual(row["body"], "Updated body.")
        finally:
            index.connection.close()

    def test_rebuild_post_index_normalizes_related_rows(self) -> None:
        self.write_post(
            "records/posts/T01.txt",
            """
            Post-ID: T01
            Board-Tags: planning alpha
            Subject: Task root
            Thread-Type: task
            Task-Status: proposed
            Task-Presentability-Impact: 0.75
            Task-Implementation-Difficulty: 0.20
            Task-Depends-On: T00 T99
            Task-Sources: todo.txt; ideas.txt

            Task body.
            """,
        )
        self.commit_all("Add task", "2026-03-17T09:00:00+00:00")

        rebuild_post_index(self.repo_root)
        index = open_post_index(self.repo_root)
        try:
            board_tags = index.connection.execute(
                "SELECT board_tag FROM post_board_tags WHERE post_id = ? ORDER BY board_tag",
                ("T01",),
            ).fetchall()
            dependencies = index.connection.execute(
                "SELECT dependency_post_id FROM post_task_dependencies WHERE post_id = ? ORDER BY dependency_post_id",
                ("T01",),
            ).fetchall()
            sources = index.connection.execute(
                "SELECT source_name FROM post_task_sources WHERE post_id = ? ORDER BY source_name",
                ("T01",),
            ).fetchall()
            self.assertEqual([row["board_tag"] for row in board_tags], ["alpha", "planning"])
            self.assertEqual([row["dependency_post_id"] for row in dependencies], ["T00", "T99"])
            self.assertEqual([row["source_name"] for row in sources], ["ideas.txt", "todo.txt"])
        finally:
            index.connection.close()

    def test_rebuild_post_index_populates_normalized_author_rows(self) -> None:
        self.write_post(
            "records/posts/root-001.txt",
            """
            Post-ID: root-001
            Board-Tags: general
            Subject: Author row

            Body.
            """,
        )
        self.commit_all("Add root", "2026-03-17T09:00:00+00:00")

        with mock.patch("forum_core.post_index.load_identity_context") as mock_context_loader:
            mock_context = mock.Mock()
            mock_context.canonical_identity_id.return_value = "openpgp:author"
            mock_context.resolved_display_name.return_value = mock.Mock(display_name="Author Name")
            mock_context_loader.return_value = mock_context
            with mock.patch("forum_core.post_index.resolve_identity_display_name", return_value="Author Name"):
                posts = load_posts(self.repo_root / "records" / "posts")
                original_post = posts[0]
                patched_post = original_post.__class__(
                    **{
                        **original_post.__dict__,
                        "identity_id": "openpgp:author",
                        "signer_fingerprint": "ABCDEF0123456789ABCDEF0123456789ABCDEF01",
                    }
                )
                with mock.patch("forum_core.post_index.load_posts", return_value=[patched_post]):
                    rebuild_post_index(self.repo_root)

        index = open_post_index(self.repo_root)
        try:
            author_row = index.connection.execute(
                """
                SELECT author_id, canonical_identity_id, display_name, display_name_source, signer_fingerprint
                FROM authors
                WHERE author_id = ?
                """,
                ("openpgp:author",),
            ).fetchone()
            post_row = index.connection.execute(
                "SELECT author_id FROM posts WHERE post_id = ?",
                ("root-001",),
            ).fetchone()
            self.assertIsNotNone(author_row)
            self.assertIsNotNone(post_row)
            assert author_row is not None
            assert post_row is not None
            self.assertEqual(author_row["canonical_identity_id"], "openpgp:author")
            self.assertEqual(author_row["display_name"], "Author Name")
            self.assertEqual(author_row["display_name_source"], "profile_update")
            self.assertEqual(author_row["signer_fingerprint"], "ABCDEF0123456789ABCDEF0123456789ABCDEF01")
            self.assertEqual(post_row["author_id"], "openpgp:author")
        finally:
            index.connection.close()

    def test_store_post_refreshes_index_after_successful_commit(self) -> None:
        payload_text = dedent(
            """
            Post-ID: root-200
            Board-Tags: general
            Subject: Stored post

            Stored body.
            """
        ).lstrip()

        post = parse_post_text(payload_text)
        store_post("create_thread", post, self.repo_root, payload_text)

        index = open_post_index(self.repo_root)
        try:
            row = index.connection.execute(
                "SELECT subject FROM posts WHERE post_id = ?",
                ("root-200",),
            ).fetchone()
            self.assertIsNotNone(row)
            assert row is not None
            self.assertEqual(row["subject"], "Stored post")
        finally:
            index.connection.close()

    def test_commit_backed_task_update_refreshes_existing_index_row(self) -> None:
        self.write_post(
            "records/posts/T01.txt",
            """
            Post-ID: T01
            Board-Tags: planning
            Subject: Task root
            Thread-Type: task
            Task-Status: proposed
            Task-Presentability-Impact: 0.50
            Task-Implementation-Difficulty: 0.20

            Initial task body.
            """,
        )
        self.commit_all("Add task", "2026-03-17T09:00:00+00:00")
        rebuild_post_index(self.repo_root)

        submit_mark_task_done("T01", self.repo_root)

        index = open_post_index(self.repo_root)
        try:
            row = index.connection.execute(
                "SELECT task_status, created_at, updated_at FROM posts WHERE post_id = ?",
                ("T01",),
            ).fetchone()
            self.assertIsNotNone(row)
            assert row is not None
            self.assertEqual(row["task_status"], "done")
            self.assertEqual(row["created_at"], "2026-03-17T09:00:00+00:00")
            self.assertIsNotNone(row["updated_at"])
            self.assertNotEqual(row["updated_at"], row["created_at"])
        finally:
            index.connection.close()


if __name__ == "__main__":
    unittest.main()
