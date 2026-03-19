from __future__ import annotations

import os
import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from unittest import mock

from forum_web import web
from forum_core.post_index import POST_INDEX_SCHEMA_VERSION, open_post_index


class PostIndexStartupTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.tempdir.name)
        (self.repo_root / "records" / "posts").mkdir(parents=True, exist_ok=True)
        (self.repo_root / "records" / "posts" / "root-001.txt").write_text(
            "Post-ID: root-001\nBoard-Tags: general\nSubject: Hello\n\nBody.\n",
            encoding="ascii",
        )

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def request(self, path: str) -> tuple[str, dict[str, str], str]:
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

        with mock.patch.dict(os.environ, {"FORUM_REPO_ROOT": str(self.repo_root)}, clear=False):
            body = b"".join(web.application(environ, start_response)).decode("utf-8")
        return response["status"], dict(response["headers"]), body

    def test_application_eagerly_initializes_post_index_once_per_repo_root(self) -> None:
        web._INDEX_STARTUP_READY_ROOTS.clear()

        with mock.patch("forum_web.web.ensure_post_index_current") as mock_ensure:
            mock_ensure.return_value = mock.Mock()

            first_status, _, _ = self.request("/instance/")
            second_status, _, _ = self.request("/instance/")

        self.assertEqual(first_status, "200 OK")
        self.assertEqual(second_status, "200 OK")
        self.assertEqual(mock_ensure.call_count, 1)
        self.assertEqual(mock_ensure.call_args.args[0], self.repo_root.resolve())

    def test_application_rebuilds_stale_index_during_startup_initialization(self) -> None:
        web._INDEX_STARTUP_READY_ROOTS.clear()

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
            index.connection.execute(
                "INSERT INTO post_index_metadata (key, value) VALUES (?, ?)",
                ("indexed_head", ""),
            )
            index.connection.commit()
        finally:
            index.connection.close()

        with mock.patch("forum_core.post_index.current_repo_head", return_value="test-head"):
            with mock.patch("forum_core.post_index.load_identity_context") as mock_context_loader:
                mock_context = mock.Mock()
                mock_context.canonical_identity_id.return_value = "openpgp:author"
                mock_context.resolved_display_name.return_value = mock.Mock(
                    display_name="Author Name",
                    record_id="profile-update-001",
                    source_identity_id="openpgp:author",
                )
                mock_context.merge_request_states = {}
                mock_context.profile_update_records = ()
                mock_context.resolution = mock.Mock()
                mock_context.resolution.members_by_canonical_identity_id = {"openpgp:author": ("openpgp:author",)}
                mock_context_loader.return_value = mock_context
                with mock.patch("forum_core.post_index.resolve_identity_display_name", return_value="Author Name"):
                    with mock.patch("forum_core.post_index.load_posts") as mock_load_posts:
                        from forum_web.repository import load_posts

                        posts = load_posts(self.repo_root / "records" / "posts")
                        original_post = posts[0]
                        patched_post = original_post.__class__(
                            **{
                                **original_post.__dict__,
                                "identity_id": "openpgp:author",
                                "signer_fingerprint": "ABCDEF0123456789ABCDEF0123456789ABCDEF01",
                            }
                        )
                        mock_load_posts.return_value = [patched_post]
                        status, _, _ = self.request("/instance/")

        self.assertEqual(status, "200 OK")

        rebuilt = open_post_index(self.repo_root)
        try:
            schema_version = rebuilt.connection.execute(
                "SELECT value FROM post_index_metadata WHERE key = ?",
                ("indexed_schema_version",),
            ).fetchone()
            author_row = rebuilt.connection.execute(
                "SELECT author_id, display_name FROM authors WHERE author_id = ?",
                ("openpgp:author",),
            ).fetchone()
            self.assertIsNotNone(schema_version)
            self.assertEqual(schema_version["value"], str(POST_INDEX_SCHEMA_VERSION))
            self.assertIsNotNone(author_row)
            self.assertEqual(author_row["display_name"], "Author Name")
        finally:
            rebuilt.connection.close()


if __name__ == "__main__":
    unittest.main()
