from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from textwrap import dedent
from unittest import mock

from forum_web.repository import load_posts
from forum_web.web import (
    activity_filter_mode_from_request,
    activity_page_from_request,
    build_posts_index,
    classify_commit_activity,
    classify_commit_area,
    describe_timestamp_display,
    fetch_recent_commits,
    fetch_recent_repository_commits,
    format_exact_timestamp,
    format_relative_timestamp,
    github_commit_url_for,
    load_activity_feed_items,
    load_activity_events,
    load_board_feed_items,
    load_thread_feed_items,
    parse_display_timestamp,
    render_timestamp_html,
    render_rss_feed,
    resolve_commit_posts,
    summarize_commit_files,
)


class SiteActivityGitLogHelpersTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.tempdir.name)
        self.run_git("init")
        self.run_git("config", "user.name", "Test User")
        self.run_git("config", "user.email", "test@example.com")
        self.run_git("remote", "add", "origin", "https://github.com/example/forum.git")

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

    def commit_paths(self, paths: list[str], message: str) -> str:
        self.run_git("add", *paths)
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

    def test_parse_display_timestamp_normalizes_zulu_and_offsets_to_utc(self) -> None:
        zulu_timestamp = parse_display_timestamp("2026-04-07T10:00:00Z")
        offset_timestamp = parse_display_timestamp("2026-04-07T06:00:00-04:00")

        self.assertEqual(zulu_timestamp, offset_timestamp)
        self.assertEqual(format_exact_timestamp(zulu_timestamp), "April 07, 2026 · 10:00:00 UTC")

    def test_format_relative_timestamp_uses_friendly_labels_for_past_and_future(self) -> None:
        now = datetime.fromisoformat("2026-04-07T12:00:00+00:00")

        self.assertEqual(
            format_relative_timestamp(datetime.fromisoformat("2026-04-07T10:00:00+00:00"), now=now),
            "2 hours ago",
        )
        self.assertEqual(
            format_relative_timestamp(datetime.fromisoformat("2026-04-07T12:30:00+00:00"), now=now),
            "in 30 minutes",
        )
        self.assertEqual(
            format_relative_timestamp(datetime.fromisoformat("2026-04-07T11:59:58+00:00"), now=now),
            "just now",
        )

    def test_describe_and_render_timestamp_display_include_relative_label_and_exact_title(self) -> None:
        now = datetime.fromisoformat("2026-04-07T12:00:00+00:00")

        display = describe_timestamp_display("2026-04-07T09:00:00Z", now=now)

        self.assertIsNotNone(display)
        assert display is not None
        self.assertEqual(display.relative_text, "3 hours ago")
        self.assertEqual(display.exact_text, "April 07, 2026 · 09:00:00 UTC")
        self.assertEqual(
            render_timestamp_html("2026-04-07T09:00:00Z", css_class="thread-timestamp", now=now),
            '<span class="thread-timestamp" title="April 07, 2026 · 09:00:00 UTC">3 hours ago</span>',
        )
        self.assertEqual(render_timestamp_html("invalid", css_class="thread-timestamp", now=now), "")

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

    def test_activity_filter_mode_defaults_to_content(self) -> None:
        self.assertEqual(activity_filter_mode_from_request(None), "content")
        self.assertEqual(activity_filter_mode_from_request(""), "content")
        self.assertEqual(activity_filter_mode_from_request("content"), "content")
        self.assertEqual(activity_filter_mode_from_request("moderation"), "moderation")
        self.assertEqual(activity_filter_mode_from_request("code"), "code")
        self.assertEqual(activity_filter_mode_from_request("unknown"), "content")

    def test_activity_page_defaults_to_one(self) -> None:
        self.assertEqual(activity_page_from_request(None), 1)
        self.assertEqual(activity_page_from_request(""), 1)
        self.assertEqual(activity_page_from_request("2"), 2)
        self.assertEqual(activity_page_from_request("0"), 1)
        self.assertEqual(activity_page_from_request("-9"), 1)
        self.assertEqual(activity_page_from_request("abc"), 1)

    def test_classify_commit_activity_distinguishes_content_moderation_and_code(self) -> None:
        content_commit = mock.Mock(files=("records/posts/root-001.txt",))
        identity_commit = mock.Mock(files=("records/identity/identity-openpgp-alpha.txt",))
        moderation_commit = mock.Mock(files=("records/moderation/pin-root-001.txt",))
        code_commit = mock.Mock(files=("forum_web/web.py",))
        mixed_commit = mock.Mock(files=("records/posts/root-001.txt", "forum_web/web.py"))

        self.assertEqual(classify_commit_activity(content_commit), "content")
        self.assertEqual(classify_commit_activity(identity_commit), "content")
        self.assertEqual(classify_commit_activity(moderation_commit), "moderation")
        self.assertEqual(classify_commit_activity(code_commit), "code")
        self.assertEqual(classify_commit_activity(mixed_commit), "code")

    def test_classify_commit_area_distinguishes_content_moderation_docs_and_code(self) -> None:
        self.assertEqual(classify_commit_area("records/posts/root-001.txt"), "content")
        self.assertEqual(classify_commit_area("records/identity/identity-openpgp-alpha.txt"), "content")
        self.assertEqual(classify_commit_area("records/moderation/pin-root-001.txt"), "moderation")
        self.assertEqual(classify_commit_area("docs/plans/feature.md"), "docs")
        self.assertEqual(classify_commit_area("forum_web/web.py"), "code")

    def test_summarize_commit_files_extracts_markdown_targets_and_area_counts(self) -> None:
        summary = summarize_commit_files(
            (
                "records/posts/root-001.txt",
                "records/moderation/pin-root-001.txt",
                "docs/plans/feature.md",
                "forum_web/web.py",
            )
        )

        self.assertEqual(summary.total_files, 4)
        self.assertEqual(summary.markdown_files, ("docs/plans/feature.md",))
        self.assertEqual(summary.post_ids, ("root-001",))
        self.assertEqual(summary.moderation_record_ids, ("pin-root-001",))
        self.assertEqual(
            dict(summary.area_counts),
            {"content": 1, "moderation": 1, "docs": 1, "code": 1},
        )

    def test_github_commit_url_for_uses_origin_remote(self) -> None:
        self.assertEqual(
            github_commit_url_for(self.repo_root, "abc123"),
            "https://github.com/example/forum/commit/abc123",
        )

    def test_github_commit_url_for_returns_none_for_non_github_remote(self) -> None:
        self.run_git("remote", "set-url", "origin", "https://gitlab.example.com/example/forum.git")

        self.assertIsNone(github_commit_url_for(self.repo_root, "abc123"))

    def test_load_activity_events_merges_content_and_moderation_in_one_timeline(self) -> None:
        self.write_record(
            "records/posts/root-001.txt",
            """
            Post-ID: root-001
            Board-Tags: general

            Body one.
            """,
        )
        self.commit("Add root-001")
        self.write_record(
            "records/moderation/pin-root-001.txt",
            """
            Record-ID: pin-root-001
            Action: pin
            Target-Type: thread
            Target-ID: root-001
            Timestamp: 2026-03-17T23:00:00Z

            Pin it.
            """,
        )
        self.commit_paths(["records/moderation/pin-root-001.txt"], "Pin root-001")

        with mock.patch("forum_web.web.fetch_recent_repository_commits") as mock_fetch:
            mock_fetch.return_value = [
                fetch_recent_repository_commits(self.repo_root, limit=2)[1],
            ]
            events = load_activity_events(self.repo_root, mode="all", page_size=5)

        self.assertEqual([event.kind for event in events.events], ["content", "moderation"])
        self.assertEqual(events.events[0].commit.subject, "Add root-001")
        self.assertEqual(events.events[1].moderation_record.record_id, "pin-root-001")

    def test_load_activity_events_filters_by_kind(self) -> None:
        self.write_record(
            "records/posts/root-001.txt",
            """
            Post-ID: root-001
            Board-Tags: general

            Body one.
            """,
        )
        self.commit("Add root-001")
        self.write_record(
            "records/moderation/pin-root-001.txt",
            """
            Record-ID: pin-root-001
            Action: pin
            Target-Type: thread
            Target-ID: root-001
            Timestamp: 2026-03-17T23:00:00Z

            Pin it.
            """,
        )
        self.commit_paths(["records/moderation/pin-root-001.txt"], "Pin root-001")

        content_events = load_activity_events(self.repo_root, mode="content", page_size=5)
        moderation_events = load_activity_events(self.repo_root, mode="moderation", page_size=5)
        code_events = load_activity_events(self.repo_root, mode="code", page_size=5)

        self.assertTrue(all(event.kind == "content" for event in content_events.events))
        self.assertTrue(all(event.kind == "moderation" for event in moderation_events.events))
        self.assertEqual(code_events.events, ())

    def test_load_activity_events_pages_content_results(self) -> None:
        for index in range(7):
            self.write_record(
                f"records/posts/root-{index:03}.txt",
                f"""
                Post-ID: root-{index:03}
                Board-Tags: general

                Body {index}.
                """,
            )
            self.commit(f"Add root-{index:03}")

        page_one = load_activity_events(self.repo_root, mode="content", page=1, page_size=3)
        page_two = load_activity_events(self.repo_root, mode="content", page=2, page_size=3)
        page_three = load_activity_events(self.repo_root, mode="content", page=3, page_size=3)

        self.assertEqual([event.commit.subject for event in page_one.events], ["Add root-006", "Add root-005", "Add root-004"])
        self.assertEqual([event.commit.subject for event in page_two.events], ["Add root-003", "Add root-002", "Add root-001"])
        self.assertEqual([event.commit.subject for event in page_three.events], ["Add root-000"])
        self.assertTrue(page_one.has_next_page)
        self.assertTrue(page_two.has_next_page)
        self.assertFalse(page_three.has_next_page)

    def test_load_activity_events_pages_all_view_after_merge(self) -> None:
        self.write_record(
            "records/posts/root-001.txt",
            """
            Post-ID: root-001
            Board-Tags: general

            Body one.
            """,
        )
        self.commit("Add root-001")
        self.write_record(
            "records/moderation/pin-root-001.txt",
            """
            Record-ID: pin-root-001
            Action: pin
            Target-Type: thread
            Target-ID: root-001
            Timestamp: 2026-03-17T23:00:00Z

            Pin it.
            """,
        )
        self.commit_paths(["records/moderation/pin-root-001.txt"], "Pin root-001")
        self.write_record("forum_web_stub.py", "print('hello')\n")
        self.commit_paths(["forum_web_stub.py"], "Add code helper")

        page_one = load_activity_events(self.repo_root, mode="all", page=1, page_size=2)
        page_two = load_activity_events(self.repo_root, mode="all", page=2, page_size=2)

        self.assertEqual([event.kind for event in page_one.events], ["code", "moderation"])
        self.assertEqual([event.kind for event in page_two.events], ["content", "moderation"])
        self.assertTrue(page_one.has_next_page)

    def test_fetch_recent_repository_commits_includes_code_changes(self) -> None:
        self.write_record(
            "records/posts/root-001.txt",
            """
            Post-ID: root-001
            Board-Tags: general

            Body one.
            """,
        )
        self.commit("Add root-001")
        self.write_record("forum_web_stub.py", "print('hello')\n")
        self.commit_paths(["forum_web_stub.py"], "Add code helper")

        commits = fetch_recent_repository_commits(self.repo_root, limit=2)

        self.assertEqual(len(commits), 2)
        self.assertEqual(commits[0].subject, "Add code helper")
        self.assertEqual(commits[0].author_name, "Test User")
        self.assertEqual(commits[0].author_email, "test@example.com")
        self.assertEqual(commits[0].short_id, commits[0].commit_id[:7])
        self.assertIn("forum_web_stub.py", commits[0].files)
        self.assertEqual(commits[0].file_summary.total_files, 1)
        self.assertEqual(dict(commits[0].file_summary.area_counts)["code"], 1)
        self.assertEqual(
            commits[0].github_url,
            f"https://github.com/example/forum/commit/{commits[0].commit_id}",
        )
        self.assertEqual(classify_commit_activity(commits[0]), "code")

    def test_render_rss_feed_outputs_channel_and_item_xml(self) -> None:
        self.write_record(
            "records/posts/root-001.txt",
            """
            Post-ID: root-001
            Board-Tags: general
            Subject: Root title

            Root body.
            """,
        )
        self.commit("Add root-001")
        xml_bytes = render_rss_feed(
            title="Example feed",
            description="Latest items",
            link="/activity/",
            items=[
                load_activity_feed_items(self.repo_root, view_mode="content", page=1, page_size=1)[0]
            ],
        )

        xml_text = xml_bytes.decode("utf-8")
        self.assertIn('<?xml version="1.0" encoding="UTF-8"?>', xml_text)
        self.assertIn("<rss version=\"2.0\">", xml_text)
        self.assertIn("<channel>", xml_text)
        self.assertIn("<title>Example feed</title>", xml_text)
        self.assertIn("<link>/activity/</link>", xml_text)
        self.assertIn("<item>", xml_text)
        self.assertIn("<guid>commit:", xml_text)

    def test_load_activity_feed_items_maps_content_moderation_and_code(self) -> None:
        self.write_record(
            "records/posts/root-001.txt",
            """
            Post-ID: root-001
            Board-Tags: general
            Subject: Root title

            Root body.
            """,
        )
        self.commit("Add root-001")
        self.write_record(
            "records/moderation/pin-root-001.txt",
            """
            Record-ID: pin-root-001
            Action: pin
            Target-Type: thread
            Target-ID: root-001
            Timestamp: 2026-03-17T23:00:00Z

            Pin it.
            """,
        )
        self.commit_paths(["records/moderation/pin-root-001.txt"], "Pin root-001")
        self.write_record("forum_web_stub.py", "print('hello')\n")
        self.commit_paths(["forum_web_stub.py"], "Add code helper")

        content_items = load_activity_feed_items(self.repo_root, view_mode="content")
        moderation_items = load_activity_feed_items(self.repo_root, view_mode="moderation")
        code_items = load_activity_feed_items(self.repo_root, view_mode="code")

        self.assertEqual(content_items[0].title, "Add root-001")
        self.assertEqual(content_items[0].link, "/threads/root-001")
        self.assertEqual(moderation_items[0].guid, "moderation:pin-root-001")
        self.assertEqual(moderation_items[0].link, "/threads/root-001")
        self.assertEqual(code_items[0].title, "Add code helper")
        self.assertTrue(code_items[0].link.endswith("/commit/" + code_items[0].guid.removeprefix("commit:")))

    def test_load_board_feed_items_filters_visible_threads_by_board(self) -> None:
        self.write_record(
            "records/posts/root-001.txt",
            """
            Post-ID: root-001
            Board-Tags: general
            Subject: General thread

            Body one.
            """,
        )
        self.write_record(
            "records/posts/root-002.txt",
            """
            Post-ID: root-002
            Board-Tags: planning
            Subject: Planning thread

            Body two.
            """,
        )
        self.commit("Add roots")

        planning_items = load_board_feed_items(self.repo_root, board_tag="planning")

        self.assertEqual([item.title for item in planning_items], ["Planning thread"])
        self.assertEqual(planning_items[0].link, "/threads/root-002")

    def test_load_thread_feed_items_returns_root_and_visible_replies(self) -> None:
        self.write_record(
            "records/posts/root-001.txt",
            """
            Post-ID: root-001
            Board-Tags: general
            Subject: Root title

            Root body.
            """,
        )
        self.write_record(
            "records/posts/reply-20260317091500-follow-up-11111111.txt",
            """
            Post-ID: reply-20260317091500-follow-up-11111111
            Board-Tags: general
            Thread-ID: root-001
            Parent-ID: root-001

            Follow-up note.
            """,
        )
        self.commit("Add thread")

        items = load_thread_feed_items(self.repo_root, thread_id="root-001")

        self.assertEqual([item.guid for item in items], ["post:root-001", "post:reply-20260317091500-follow-up-11111111"])
        self.assertEqual(items[0].link, "/threads/root-001")
        self.assertEqual(items[1].link, "/posts/reply-20260317091500-follow-up-11111111")


if __name__ == "__main__":
    unittest.main()
