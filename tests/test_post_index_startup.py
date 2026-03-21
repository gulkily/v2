from __future__ import annotations

import os
import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from unittest import mock

from forum_web import web
from forum_core.post_index import POST_INDEX_SCHEMA_VERSION, PostIndexReadiness, open_post_index


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

    def request(self, path: str, *, query_string: str = "", extra_environ: dict[str, object] | None = None) -> tuple[str, dict[str, str], str]:
        environ = {
            "PATH_INFO": path,
            "QUERY_STRING": query_string,
            "REQUEST_METHOD": "GET",
            "CONTENT_LENGTH": "0",
            "wsgi.input": BytesIO(b""),
        }
        if extra_environ:
            environ.update(extra_environ)
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

    def test_board_request_shows_refresh_page_when_startup_index_is_stale(self) -> None:
        web._INDEX_STARTUP_READY_ROOTS.clear()

        readiness = PostIndexReadiness(
            expected_post_count=1,
            indexed_post_count=0,
            indexed_head=None,
            current_head="test-head",
            indexed_schema_version=str(POST_INDEX_SCHEMA_VERSION),
            count_mismatch=True,
            head_mismatch=True,
            schema_mismatch=False,
        )
        with self.assertLogs("forum_web.web", level="WARNING") as captured_logs:
            with mock.patch("forum_web.web.post_index_readiness", return_value=readiness):
                with mock.patch("forum_web.web.rebuild_post_index") as mock_rebuild:
                    with mock.patch("forum_web.web.ensure_runtime_post_index_startup") as mock_startup:
                        status, _, body = self.request("/")

        self.assertEqual(status, "200 OK")
        self.assertIn("Refreshing the forum...", body)
        self.assertIn("prefers-color-scheme: dark", body)
        self.assertNotIn("recent slow operations", body)
        self.assertNotIn('/assets/site.css', body)
        self.assertNotIn('/assets/username_claim_cta.js', body)
        self.assertTrue(any("post index rebuild triggered for" in message for message in captured_logs.output))
        mock_rebuild.assert_called_once_with(self.repo_root.resolve())
        mock_startup.assert_not_called()

    def test_board_request_shows_refresh_page_when_index_database_is_missing(self) -> None:
        web._INDEX_STARTUP_READY_ROOTS.clear()

        readiness = PostIndexReadiness(
            expected_post_count=1,
            indexed_post_count=0,
            indexed_head=None,
            current_head="test-head",
            indexed_schema_version=None,
            count_mismatch=True,
            head_mismatch=True,
            schema_mismatch=True,
        )
        with self.assertLogs("forum_web.web", level="WARNING") as captured_logs:
            with mock.patch("forum_web.web.post_index_readiness", return_value=readiness):
                with mock.patch("forum_web.web.rebuild_post_index") as mock_rebuild:
                    with mock.patch("forum_web.web.ensure_runtime_post_index_startup") as mock_startup:
                        status, _, body = self.request("/")

        self.assertEqual(status, "200 OK")
        self.assertIn("Refreshing the forum...", body)
        self.assertIn("A small interval of stillness while the next page arrives.", body)
        self.assertTrue(any("post index rebuild triggered for" in message for message in captured_logs.output))
        mock_rebuild.assert_called_once_with(self.repo_root.resolve())
        mock_startup.assert_not_called()

    def test_profile_request_shows_refresh_page_when_index_drifts_after_startup(self) -> None:
        web._INDEX_STARTUP_READY_ROOTS.clear()
        web._INDEX_STARTUP_READY_ROOTS.add(self.repo_root.resolve())

        readiness = PostIndexReadiness(
            expected_post_count=1,
            indexed_post_count=1,
            indexed_head="old-head",
            current_head="new-head",
            indexed_schema_version=str(POST_INDEX_SCHEMA_VERSION),
            count_mismatch=False,
            head_mismatch=True,
            schema_mismatch=False,
        )
        with mock.patch("forum_web.web.post_index_readiness", return_value=readiness):
            with mock.patch("forum_web.web.rebuild_post_index") as mock_rebuild:
                with mock.patch("forum_web.web.ensure_runtime_post_index_startup") as mock_startup:
                    status, _, body = self.request("/profiles/openpgp-alpha")

        self.assertEqual(status, "200 OK")
        self.assertIn("Refreshing the forum...", body)
        self.assertIn("A small interval of stillness while the next page arrives.", body)
        self.assertIn("/profiles/openpgp-alpha", body)
        mock_rebuild.assert_called_once_with(self.repo_root.resolve())
        mock_startup.assert_called_once_with(self.repo_root)

    def test_refresh_page_retry_link_preserves_query_string(self) -> None:
        web._INDEX_STARTUP_READY_ROOTS.clear()
        web._INDEX_STARTUP_READY_ROOTS.add(self.repo_root.resolve())

        readiness = PostIndexReadiness(
            expected_post_count=1,
            indexed_post_count=1,
            indexed_head="old-head",
            current_head="new-head",
            indexed_schema_version=str(POST_INDEX_SCHEMA_VERSION),
            count_mismatch=False,
            head_mismatch=True,
            schema_mismatch=False,
        )
        with mock.patch("forum_web.web.post_index_readiness", return_value=readiness):
            with mock.patch("forum_web.web.rebuild_post_index"):
                with mock.patch("forum_web.web.ensure_runtime_post_index_startup"):
                    status, _, body = self.request("/profiles/openpgp-alpha", query_string="self=1")

        self.assertEqual(status, "200 OK")
        self.assertIn('/profiles/openpgp-alpha?self=1', body)

    def test_cgi_style_request_returns_buffered_rebuild_status_contract(self) -> None:
        web._INDEX_STARTUP_READY_ROOTS.clear()

        readiness = PostIndexReadiness(
            expected_post_count=1,
            indexed_post_count=0,
            indexed_head=None,
            current_head="test-head",
            indexed_schema_version=None,
            count_mismatch=True,
            head_mismatch=True,
            schema_mismatch=True,
        )
        with mock.patch("forum_web.web.post_index_readiness", return_value=readiness):
            with mock.patch("forum_web.web.rebuild_post_index") as mock_rebuild:
                with mock.patch("forum_web.web.ensure_runtime_post_index_startup") as mock_startup:
                    status, headers, body = self.request("/", extra_environ={"wsgi.run_once": True})

        self.assertEqual(status, "503 Service Unavailable")
        self.assertEqual(headers[web.POST_INDEX_REBUILD_STATUS_HEADER], "required")
        self.assertEqual(headers[web.POST_INDEX_REBUILD_TARGET_HEADER], "/")
        self.assertEqual(headers[web.POST_INDEX_REBUILD_REQUEST_HEADER], "/?__forum_rebuild=1")
        self.assertIn("Refreshing the forum...", body)
        mock_rebuild.assert_not_called()
        mock_startup.assert_not_called()

    def test_cgi_style_request_preserves_query_string_in_buffered_rebuild_status_contract(self) -> None:
        web._INDEX_STARTUP_READY_ROOTS.clear()

        readiness = PostIndexReadiness(
            expected_post_count=1,
            indexed_post_count=1,
            indexed_head="old-head",
            current_head="new-head",
            indexed_schema_version=str(POST_INDEX_SCHEMA_VERSION),
            count_mismatch=False,
            head_mismatch=True,
            schema_mismatch=False,
        )
        with mock.patch("forum_web.web.post_index_readiness", return_value=readiness):
            with mock.patch("forum_web.web.ensure_runtime_post_index_startup") as mock_startup:
                status, headers, _ = self.request(
                    "/profiles/openpgp-alpha",
                    query_string="self=1",
                    extra_environ={"wsgi.run_once": True},
                )

        self.assertEqual(status, "503 Service Unavailable")
        self.assertEqual(headers[web.POST_INDEX_REBUILD_TARGET_HEADER], "/profiles/openpgp-alpha?self=1")
        self.assertEqual(
            headers[web.POST_INDEX_REBUILD_REQUEST_HEADER],
            "/profiles/openpgp-alpha?self=1&__forum_rebuild=1",
        )
        mock_startup.assert_not_called()

    def test_cgi_style_rebuild_request_bypasses_buffered_status_contract(self) -> None:
        web._INDEX_STARTUP_READY_ROOTS.clear()

        readiness = PostIndexReadiness(
            expected_post_count=1,
            indexed_post_count=0,
            indexed_head=None,
            current_head="test-head",
            indexed_schema_version=None,
            count_mismatch=True,
            head_mismatch=True,
            schema_mismatch=True,
        )
        with mock.patch("forum_web.web.post_index_readiness", return_value=readiness):
            with mock.patch("forum_web.web.ensure_runtime_post_index_startup") as mock_startup:
                status, _, body = self.request(
                    "/",
                    query_string="__forum_rebuild=1",
                    extra_environ={"wsgi.run_once": True},
                )

        self.assertEqual(status, "200 OK")
        self.assertNotIn("Refreshing the forum...", body)
        mock_startup.assert_called_once_with(self.repo_root)


if __name__ == "__main__":
    unittest.main()
