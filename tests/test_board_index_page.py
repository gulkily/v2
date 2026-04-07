from __future__ import annotations

import os
import unittest
from io import BytesIO
from unittest import mock

from forum_core.post_index import ensure_post_index_current
from tests.helpers import ForumRepoTestCase


class BoardIndexPageTests(ForumRepoTestCase):
    def setUp(self) -> None:
        super().setUp()
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
            "records/posts/root-003.txt",
            """
            Post-ID: root-003
            Board-Tags: general
            Subject: Same words

            Same words
            """,
        )

    def init_git_repo(self) -> None:
        super().init_git_repo()

    def commit_posts(self, message: str, timestamp: str) -> None:
        env = {
            "PATH": os.environ["PATH"],
            "GIT_AUTHOR_DATE": timestamp,
            "GIT_COMMITTER_DATE": timestamp,
        }
        self.run_git("add", "records/posts", env=env)
        self.run_git("commit", "-m", message, env=env)

    def get(self, path: str, query_string: str = "") -> tuple[str, dict[str, str], str]:
        status, headers, body = self.request(path, query_string=query_string)
        return status, headers, str(body)

    def test_board_index_uses_shared_page_shell(self) -> None:
        status, headers, body = self.get("/")

        self.assertEqual(status, "200 OK")
        self.assertEqual(headers["Content-Type"], "text/html; charset=utf-8")
        self.assertIn('class="site-header site-header--page"', body)
        self.assertIn('class="site-footer"', body)
        self.assertNotIn("Board Index", body)
        self.assertNotIn("Threads worth opening", body)
        self.assertNotIn(">Visible threads<", body)
        self.assertIn("/threads/root-001", body)
        self.assertIn("Hello world", body)
        self.assertIn("First line preview.", body)
        self.assertIn("posts loaded", body)
        self.assertIn("board tags", body)
        self.assertTrue(body.index("/threads/root-001") < body.index("posts loaded"))
        self.assertNotIn('class="front-header"', body)
        self.assertNotIn('class="front-layout"', body)
        self.assertNotIn("Kindness first.", body)
        self.assertIn('<link rel="icon" type="image/svg+xml" href="/assets/favicon.svg">', body)
        self.assertIn('<link rel="icon" href="/favicon.ico" sizes="any">', body)
        self.assertIn('<link rel="shortcut icon" href="/favicon.ico">', body)
        self.assertIn('rel="alternate" type="application/rss+xml"', body)
        self.assertIn('href="/?format=rss"', body)
        self.assertNotIn('thread-chip--rss', body)

    def test_board_index_kindness_header_flag_defaults_off_and_can_be_enabled(self) -> None:
        _, _, default_body = self.get("/")

        self.assertNotIn('class="site-header-band"', default_body)
        self.assertNotIn("Kindness first.", default_body)

        status, _, enabled_body = self.request("/", extra_env={"FORUM_ENABLE_KINDNESS_HEADER": "1"})

        self.assertEqual(status, "200 OK")
        self.assertIn('class="site-header-band"', enabled_body)
        self.assertIn("Kindness first.", enabled_body)

    def test_board_index_can_disable_username_claim_cta_via_feature_flag(self) -> None:
        status, _, body = self.request("/", extra_env={"FORUM_ENABLE_USERNAME_CLAIM_CTA": "0"})

        self.assertEqual(status, "200 OK")
        self.assertNotIn('data-username-claim-cta', body)
        self.assertNotIn('/assets/username_claim_cta.js', body)
        self.assertNotIn("Choose your username", body)

    def test_board_index_uses_configured_site_title_when_present(self) -> None:
        status, _, body = self.request("/", extra_env={"FORUM_SITE_TITLE": "ZenMemes Forum"})

        self.assertEqual(status, "200 OK")
        self.assertIn("<title>ZenMemes Forum</title>", body)
        self.assertIn('class="site-header-title"><a href="/">ZenMemes Forum</a>', body)

    def test_board_index_preserves_key_destination_links(self) -> None:
        status, _, body = self.get("/")

        self.assertEqual(status, "200 OK")
        self.assertEqual(body.count('aria-current="page"'), 1)
        self.assertIn('<a href="/" aria-current="page">Home</a>', body)
        self.assertIn('/compose/thread', body)
        self.assertIn('/instance/', body)
        self.assertIn('/activity/', body)
        self.assertIn('data-profile-nav-link', body)
        self.assertIn('data-profile-nav-state="unresolved"', body)
        self.assertIn('aria-disabled="true"', body)
        self.assertIn('tabindex="-1"', body)
        self.assertIn('>My profile</a>', body)
        self.assertIn('/assets/profile_nav.js', body)
        self.assertIn('data-username-claim-cta', body)

    def test_board_index_source_uses_multiline_stats_and_thread_rows(self) -> None:
        status, _, body = self.get("/")

        self.assertEqual(status, "200 OK")
        self.assertIn('<div class="stat-grid">\n', body)
        self.assertIn('<article class="board-index-thread-row">\n', body)
        self.assertIn('<p>First line preview.</p>\n', body)
        self.assertIn('</article>\n<article class="board-index-thread-row">', body)
        self.assertIn('/assets/username_claim_cta.js', body)
        self.assertIn('Choose your username', body)

    def test_board_index_uses_resolved_thread_title_when_update_record_exists(self) -> None:
        self.write_record(
            "records/thread-title-updates/thread-title-update-001.txt",
            """
            Record-ID: thread-title-update-001
            Thread-ID: root-001
            Timestamp: 2026-03-28T12:00:00Z

            Renamed thread
            """,
        )

        status, _, body = self.get("/")

        self.assertEqual(status, "200 OK")
        self.assertIn("Renamed thread", body)
        self.assertNotIn(">Hello world<", body)

    def test_board_index_suppresses_default_listing_metadata(self) -> None:
        status, _, body = self.get("/")

        self.assertEqual(status, "200 OK")
        self.assertNotIn(">root-001<", body)
        self.assertNotIn(">root-002<", body)
        self.assertNotIn(">root-003<", body)
        self.assertIn("[general] [meta]", body)
        self.assertNotIn(">Same words</a></h3><p class=\"board-index-thread-tags\">[general]</p>", body)
        self.assertNotIn(">Same words</a></h3><p>Same words</p>", body)
        self.assertNotIn("0 replies", body)
        self.assertIn("1 reply", body)

    def test_board_index_orders_threads_by_commit_recency_when_index_is_available(self) -> None:
        self.init_git_repo()
        self.commit_posts("Add roots", "2026-03-17T09:00:00+00:00")

        self.write_record(
            "records/posts/root-001.txt",
            """
            Post-ID: root-001
            Board-Tags: general meta
            Subject: Hello world

            Freshly updated body.
            """,
        )
        self.commit_posts("Update root-001", "2026-03-17T12:00:00+00:00")
        ensure_post_index_current(self.repo_root)

        status, _, body = self.get("/")

        self.assertEqual(status, "200 OK")
        self.assertTrue(body.index("/threads/root-001") < body.index("/threads/root-002"))

    def test_board_index_shows_friendly_last_active_timestamp_with_exact_title(self) -> None:
        self.init_git_repo()
        self.commit_posts("Add roots", "2026-03-17T09:00:00+00:00")

        self.write_record(
            "records/posts/root-001.txt",
            """
            Post-ID: root-001
            Board-Tags: general meta
            Subject: Hello world

            Freshly updated body.
            """,
        )
        self.commit_posts("Update root-001", "2026-03-17T12:00:00+00:00")
        ensure_post_index_current(self.repo_root)

        status, _, body = self.get("/")

        self.assertEqual(status, "200 OK")
        self.assertIn('last active <span class="friendly-timestamp" title="March 17, 2026 · 12:00:00 UTC">', body)
        self.assertIn("ago</span>", body)

    def test_board_index_omits_last_active_timestamp_when_indexed_timestamps_are_unavailable(self) -> None:
        status, _, body = self.get("/")

        self.assertEqual(status, "200 OK")
        self.assertNotIn("last active", body)

    def test_board_index_route_can_render_rss_feed(self) -> None:
        self.init_git_repo()
        self.commit_posts("Add roots", "2026-03-17T09:00:00+00:00")

        status, headers, body = self.get("/", "format=rss")

        self.assertEqual(status, "200 OK")
        self.assertEqual(headers["Content-Type"], "application/rss+xml; charset=utf-8")
        self.assertIn('<?xml version="1.0" encoding="UTF-8"?>', body)
        self.assertIn("threads</title>", body)
        self.assertIn("<link>/</link>", body)
        self.assertIn("<guid>thread:root-001</guid>", body)

    def test_board_index_rss_can_filter_to_one_board_tag(self) -> None:
        self.init_git_repo()
        self.commit_posts("Add roots", "2026-03-17T09:00:00+00:00")

        status, headers, body = self.get("/", "board_tag=planning&format=rss")

        self.assertEqual(status, "200 OK")
        self.assertEqual(headers["Content-Type"], "application/rss+xml; charset=utf-8")
        self.assertIn("/planning/ threads</title>", body)
        self.assertIn("<link>/?board_tag=planning</link>", body)
        self.assertIn("Planning thread", body)
        self.assertNotIn("Hello world", body)

    def test_board_index_rss_rejects_unknown_board_tag(self) -> None:
        self.init_git_repo()
        self.commit_posts("Add roots", "2026-03-17T09:00:00+00:00")

        status, headers, body = self.get("/", "board_tag=unknown&format=rss")

        self.assertEqual(status, "400 Bad Request")
        self.assertEqual(headers["Content-Type"], "text/plain; charset=utf-8")
        self.assertIn("unknown board_tag: unknown", body)


if __name__ == "__main__":
    unittest.main()
