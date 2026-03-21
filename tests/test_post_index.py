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
    PostCommitTimestamps,
    PostIndexReadiness,
    author_id_for_post,
    author_row_for_post,
    current_post_index_schema_version,
    ensure_post_index_current,
    get_index_metadata,
    index_schema_is_current,
    load_indexed_authors,
    load_indexed_identity_members,
    load_indexed_root_posts,
    load_indexed_username_roots,
    open_post_index,
    post_commit_timestamps,
    post_index_readiness,
    post_index_path,
    rebuild_post_index,
)
from forum_core.identity import build_identity_id
from forum_core.merge_requests import MergeRequestState
from forum_core.profile_updates import parse_profile_update_text
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

    def test_ensure_post_index_current_rebuilds_when_schema_backfill_metadata_is_missing(self) -> None:
        (self.repo_root / "records" / "posts").mkdir(parents=True, exist_ok=True)
        (self.repo_root / "records" / "posts" / "root-001.txt").write_text(
            dedent(
                """
                Post-ID: root-001
                Board-Tags: general
                Subject: Hello

                Body.
                """
            ).lstrip(),
            encoding="ascii",
        )
        subprocess.run(["git", "-C", str(self.repo_root), "init"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        subprocess.run(["git", "-C", str(self.repo_root), "config", "user.name", "Test User"], check=True)
        subprocess.run(["git", "-C", str(self.repo_root), "config", "user.email", "test@example.com"], check=True)
        subprocess.run(["git", "-C", str(self.repo_root), "add", "records/posts"], check=True)
        subprocess.run(["git", "-C", str(self.repo_root), "commit", "-m", "initial"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        index = open_post_index(self.repo_root)
        try:
            index.connection.execute(
                """
                INSERT INTO posts (post_id, relative_path, subject, thread_id, parent_id, root_thread_id, body, is_root)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                ("root-001", "records/posts/root-001.txt", "Hello", None, None, "root-001", "Body.", 1),
            )
            index.connection.execute(
                "INSERT INTO post_index_metadata (key, value) VALUES (?, ?)",
                ("indexed_post_count", "1"),
            )
            head = subprocess.run(
                ["git", "-C", str(self.repo_root), "rev-parse", "HEAD"],
                check=True,
                stdout=subprocess.PIPE,
                text=True,
            ).stdout.strip()
            index.connection.execute(
                "INSERT INTO post_index_metadata (key, value) VALUES (?, ?)",
                ("indexed_head", head),
            )
            index.connection.commit()
            self.assertFalse(index_schema_is_current(index.connection))
        finally:
            index.connection.close()

        rebuilt = ensure_post_index_current(self.repo_root)
        try:
            self.assertEqual(
                get_index_metadata(rebuilt.connection, "indexed_schema_version"),
                str(POST_INDEX_SCHEMA_VERSION),
            )
            self.assertTrue(index_schema_is_current(rebuilt.connection))
        finally:
            rebuilt.connection.close()

    def test_post_index_readiness_reports_current_index_without_rebuild(self) -> None:
        (self.repo_root / "records" / "posts").mkdir(parents=True, exist_ok=True)
        (self.repo_root / "records" / "posts" / "root-001.txt").write_text(
            "Post-ID: root-001\nBoard-Tags: general\nSubject: Hello\n\nBody.\n",
            encoding="ascii",
        )
        subprocess.run(["git", "-C", str(self.repo_root), "init"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        subprocess.run(["git", "-C", str(self.repo_root), "config", "user.name", "Test User"], check=True)
        subprocess.run(["git", "-C", str(self.repo_root), "config", "user.email", "test@example.com"], check=True)
        subprocess.run(["git", "-C", str(self.repo_root), "add", "records/posts"], check=True)
        subprocess.run(["git", "-C", str(self.repo_root), "commit", "-m", "initial"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        rebuild_post_index(self.repo_root)

        readiness = post_index_readiness(self.repo_root)

        self.assertIsInstance(readiness, PostIndexReadiness)
        self.assertFalse(readiness.requires_rebuild)
        self.assertFalse(readiness.count_mismatch)
        self.assertFalse(readiness.head_mismatch)
        self.assertFalse(readiness.schema_mismatch)

    def test_post_index_readiness_reports_stale_index_when_head_drifts(self) -> None:
        (self.repo_root / "records" / "posts").mkdir(parents=True, exist_ok=True)
        (self.repo_root / "records" / "posts" / "root-001.txt").write_text(
            "Post-ID: root-001\nBoard-Tags: general\nSubject: Hello\n\nBody.\n",
            encoding="ascii",
        )
        subprocess.run(["git", "-C", str(self.repo_root), "init"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        subprocess.run(["git", "-C", str(self.repo_root), "config", "user.name", "Test User"], check=True)
        subprocess.run(["git", "-C", str(self.repo_root), "config", "user.email", "test@example.com"], check=True)
        subprocess.run(["git", "-C", str(self.repo_root), "add", "records/posts"], check=True)
        subprocess.run(["git", "-C", str(self.repo_root), "commit", "-m", "initial"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        rebuild_post_index(self.repo_root)
        subprocess.run(
            ["git", "-C", str(self.repo_root), "commit", "--allow-empty", "-m", "head drift"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        readiness = post_index_readiness(self.repo_root)

        self.assertTrue(readiness.requires_rebuild)
        self.assertFalse(readiness.count_mismatch)
        self.assertTrue(readiness.head_mismatch)
        self.assertFalse(readiness.schema_mismatch)


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
                members_by_canonical_identity_id={"openpgp:canonical": ("openpgp:canonical",)},
            ),
            profile_update_records=(),
            merge_request_records=(),
            merge_request_states=(),
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

    def commit_paths(self, message: str, timestamp: str, *paths: str) -> None:
        env = {
            "GIT_AUTHOR_DATE": timestamp,
            "GIT_COMMITTER_DATE": timestamp,
            "PATH": os.environ["PATH"],
        }
        self.run_git("add", *paths, env=env)
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

    def test_post_commit_timestamps_uses_shared_per_path_helper_for_full_rebuild(self) -> None:
        self.write_post(
            "records/posts/root-001.txt",
            """
            Post-ID: root-001
            Board-Tags: general
            Subject: First root

            First body.
            """,
        )
        self.write_post(
            "records/posts/root-002.txt",
            """
            Post-ID: root-002
            Board-Tags: general
            Subject: Second root

            Second body.
            """,
        )
        self.commit_all("Add roots", "2026-03-17T10:00:00+00:00")

        with mock.patch("forum_core.post_index._full_rebuild_timestamp_worker_count", return_value=1), mock.patch(
            "forum_core.post_index._post_commit_timestamps_for_relative_path",
            side_effect=[
                ("root-001", PostCommitTimestamps(created_at="2026-03-17T10:00:00+00:00", updated_at="2026-03-17T10:00:00+00:00")),
                ("root-002", PostCommitTimestamps(created_at="2026-03-17T10:00:00+00:00", updated_at="2026-03-17T10:00:00+00:00")),
            ],
        ) as mock_path_helper:
            timestamps = post_commit_timestamps(self.repo_root)

        self.assertEqual(
            timestamps,
            {
                "root-001": PostCommitTimestamps(
                    created_at="2026-03-17T10:00:00+00:00",
                    updated_at="2026-03-17T10:00:00+00:00",
                ),
                "root-002": PostCommitTimestamps(
                    created_at="2026-03-17T10:00:00+00:00",
                    updated_at="2026-03-17T10:00:00+00:00",
                ),
            },
        )
        self.assertEqual(mock_path_helper.call_count, 2)

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

    def test_load_indexed_root_posts_returns_coherent_timestamps_after_rebuild(self) -> None:
        self.write_post(
            "records/posts/root-001.txt",
            """
            Post-ID: root-001
            Board-Tags: general
            Subject: First root

            First body.
            """,
        )
        self.write_post(
            "records/posts/root-002.txt",
            """
            Post-ID: root-002
            Board-Tags: planning
            Subject: Second root

            Second body.
            """,
        )
        self.commit_all("Add roots", "2026-03-17T10:00:00+00:00")

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

        root_posts = load_indexed_root_posts(self.repo_root)

        self.assertEqual(root_posts["root-001"].created_at, "2026-03-17T10:00:00+00:00")
        self.assertEqual(root_posts["root-001"].updated_at, "2026-03-17T12:00:00+00:00")
        self.assertEqual(root_posts["root-002"].created_at, "2026-03-17T10:00:00+00:00")
        self.assertEqual(root_posts["root-002"].updated_at, "2026-03-17T10:00:00+00:00")

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
            mock_context.resolution.members_by_canonical_identity_id = {}
            mock_context.merge_request_states = ()
            mock_context.profile_update_records = ()
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

    def test_load_indexed_author_helpers_expose_normalized_author_data(self) -> None:
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
            mock_context.resolution.members_by_canonical_identity_id = {}
            mock_context.merge_request_states = ()
            mock_context.profile_update_records = ()
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

        authors = load_indexed_authors(self.repo_root)
        root_posts = load_indexed_root_posts(self.repo_root)

        self.assertEqual(
            authors["openpgp:author"],
            IndexedAuthorRow(
                author_id="openpgp:author",
                canonical_identity_id="openpgp:author",
                display_name="Author Name",
                display_name_source="profile_update",
                signer_fingerprint="ABCDEF0123456789ABCDEF0123456789ABCDEF01",
            ),
        )
        self.assertEqual(root_posts["root-001"].author_id, "openpgp:author")

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

    def test_incremental_refresh_uses_touched_path_timestamps_only(self) -> None:
        first_payload_text = dedent(
            """
            Post-ID: root-200
            Board-Tags: general
            Subject: Stored post

            Stored body.
            """
        ).lstrip()
        first_post = parse_post_text(first_payload_text)
        store_post("create_thread", first_post, self.repo_root, first_payload_text)

        second_payload_text = dedent(
            """
            Post-ID: root-201
            Board-Tags: general
            Subject: Incremental stored post

            Stored body.
            """
        ).lstrip()
        second_post = parse_post_text(second_payload_text)

        with mock.patch(
            "forum_core.post_index.post_commit_timestamps",
            side_effect=AssertionError("full timestamp scan should not run during incremental refresh"),
        ), mock.patch(
            "forum_core.post_index.post_commit_timestamps_for_paths",
            return_value={
                "root-201": PostCommitTimestamps(
                    created_at="2026-03-18T12:00:00+00:00",
                    updated_at="2026-03-18T12:00:00+00:00",
                )
            },
        ) as mock_timestamps:
            store_post("create_thread", second_post, self.repo_root, second_payload_text)

        mock_timestamps.assert_called_once_with(
            self.repo_root,
            relative_paths=("records/posts/root-201.txt",),
        )
        index = open_post_index(self.repo_root)
        try:
            row = index.connection.execute(
                "SELECT created_at, updated_at FROM posts WHERE post_id = ?",
                ("root-201",),
            ).fetchone()
            self.assertIsNotNone(row)
            assert row is not None
            self.assertEqual(row["created_at"], "2026-03-18T12:00:00+00:00")
            self.assertEqual(row["updated_at"], "2026-03-18T12:00:00+00:00")
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

    def test_rebuild_post_index_caches_identity_members_username_claims_and_roots(self) -> None:
        first_path = self.repo_root / "records" / "profile-updates" / "profile-update-alpha.txt"
        second_path = self.repo_root / "records" / "profile-updates" / "profile-update-beta.txt"
        first_path.parent.mkdir(parents=True, exist_ok=True)
        first_path.write_text(
            dedent(
                """
                Record-ID: profile-update-alpha
                Action: set_display_name
                Source-Identity-ID: openpgp:alpha
                Timestamp: 2026-03-17T09:00:00Z

                shared-name
                """
            ).lstrip(),
            encoding="ascii",
        )
        self.commit_paths(
            "Add alpha profile update",
            "2026-03-17T09:00:00+00:00",
            "records/profile-updates/profile-update-alpha.txt",
        )

        second_path.write_text(
            dedent(
                """
                Record-ID: profile-update-beta
                Action: set_display_name
                Source-Identity-ID: openpgp:beta
                Timestamp: 2026-03-17T10:00:00Z

                shared-name
                """
            ).lstrip(),
            encoding="ascii",
        )
        self.commit_paths(
            "Add beta profile update",
            "2026-03-17T10:00:00+00:00",
            "records/profile-updates/profile-update-beta.txt",
        )

        alpha_record = parse_profile_update_text(first_path.read_text(encoding="ascii"), source_path=first_path)
        beta_record = parse_profile_update_text(second_path.read_text(encoding="ascii"), source_path=second_path)
        identity_context = IdentityContext(
            bootstraps_by_identity_id={},
            resolution=SimpleNamespace(
                canonical_identity_id=lambda identity_id: {
                    "openpgp:alpha": "openpgp:alpha",
                    "openpgp:beta": "openpgp:beta",
                }.get(identity_id),
                member_identity_ids=lambda identity_id: {
                    "openpgp:alpha": ("openpgp:alpha",),
                    "openpgp:beta": ("openpgp:beta",),
                }.get(identity_id, ()),
                members_by_canonical_identity_id={
                    "openpgp:alpha": ("openpgp:alpha",),
                    "openpgp:beta": ("openpgp:beta",),
                },
            ),
            profile_update_records=(alpha_record, beta_record),
            merge_request_records=(),
            merge_request_states=(
                MergeRequestState(
                    requester_identity_id="openpgp:alpha",
                    target_identity_id="openpgp:beta",
                    latest_request_record_id="merge-request-001",
                    latest_request_timestamp="2026-03-17T11:00:00Z",
                    latest_request_note="merge",
                    latest_response_action="approve_merge",
                    latest_response_record_id="merge-request-002",
                    latest_response_timestamp="2026-03-17T11:05:00Z",
                    approved_by_target=True,
                    approved_by_moderator=False,
                    dismissed=False,
                    active_merge=True,
                    pending=False,
                ),
            ),
        )

        with mock.patch("forum_core.post_index.load_posts", return_value=[]):
            with mock.patch("forum_core.post_index.load_identity_context", return_value=identity_context):
                rebuild_post_index(self.repo_root)

        members = load_indexed_identity_members(self.repo_root)
        roots = load_indexed_username_roots(self.repo_root)
        index = open_post_index(self.repo_root)
        try:
            edges = index.connection.execute(
                """
                SELECT source_identity_id, target_identity_id, edge_kind
                FROM active_merge_edges
                ORDER BY source_identity_id, target_identity_id
                """
            ).fetchall()
            claims = index.connection.execute(
                """
                SELECT canonical_identity_id, username_token, claim_record_id, claim_commit_rank
                FROM current_username_claims
                ORDER BY canonical_identity_id
                """
            ).fetchall()
            self.assertEqual(members["openpgp:alpha"], ("openpgp:alpha",))
            self.assertEqual(members["openpgp:beta"], ("openpgp:beta",))
            self.assertEqual(
                [(row["source_identity_id"], row["target_identity_id"], row["edge_kind"]) for row in edges],
                [
                    ("openpgp:alpha", "openpgp:beta", "approved_merge_request"),
                    ("openpgp:beta", "openpgp:alpha", "approved_merge_request"),
                ],
            )
            self.assertEqual(
                [(row["canonical_identity_id"], row["username_token"], row["claim_record_id"]) for row in claims],
                [
                    ("openpgp:alpha", "shared-name", "profile-update-alpha"),
                    ("openpgp:beta", "shared-name", "profile-update-beta"),
                ],
            )
            self.assertEqual(roots["shared-name"].canonical_identity_id, "openpgp:alpha")
            self.assertEqual(roots["shared-name"].claim_record_id, "profile-update-alpha")
            self.assertLess(
                roots["shared-name"].claim_commit_rank,
                next(row["claim_commit_rank"] for row in claims if row["canonical_identity_id"] == "openpgp:beta"),
            )
        finally:
            index.connection.close()


if __name__ == "__main__":
    unittest.main()
