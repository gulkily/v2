from __future__ import annotations

import os
import sqlite3
import subprocess
import tempfile
import unittest
from pathlib import Path
from textwrap import dedent

from forum_core.post_index import (
    POST_INDEX_SCHEMA_VERSION,
    current_post_index_schema_version,
    open_post_index,
    post_index_path,
    rebuild_post_index,
)


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


if __name__ == "__main__":
    unittest.main()
