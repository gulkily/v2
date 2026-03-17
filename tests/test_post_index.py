from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from forum_core.post_index import (
    POST_INDEX_SCHEMA_VERSION,
    current_post_index_schema_version,
    open_post_index,
    post_index_path,
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


if __name__ == "__main__":
    unittest.main()
