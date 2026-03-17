from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from textwrap import dedent
from unittest import mock

from forum_web.repository import load_posts
from forum_web.web import (
    activity_filter_mode_from_request,
    build_posts_index,
    classify_commit_activity,
    fetch_recent_commits,
    fetch_recent_repository_commits,
    load_activity_events,
    resolve_commit_posts,
)


class SiteActivityGitLogHelpersTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.tempdir.name)
        self.run_git("init")
        self.run_git("config", "user.name", "Test User")
        self.run_git("config", "user.email", "test@example.com")

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

    def test_activity_filter_mode_defaults_to_all(self) -> None:
        self.assertEqual(activity_filter_mode_from_request(None), "all")
        self.assertEqual(activity_filter_mode_from_request(""), "all")
        self.assertEqual(activity_filter_mode_from_request("content"), "content")
        self.assertEqual(activity_filter_mode_from_request("moderation"), "moderation")
        self.assertEqual(activity_filter_mode_from_request("code"), "code")
        self.assertEqual(activity_filter_mode_from_request("unknown"), "all")

    def test_classify_commit_activity_distinguishes_content_moderation_and_code(self) -> None:
        content_commit = mock.Mock(files=("records/posts/root-001.txt",))
        moderation_commit = mock.Mock(files=("records/moderation/pin-root-001.txt",))
        code_commit = mock.Mock(files=("forum_web/web.py",))
        mixed_commit = mock.Mock(files=("records/posts/root-001.txt", "forum_web/web.py"))

        self.assertEqual(classify_commit_activity(content_commit), "content")
        self.assertEqual(classify_commit_activity(moderation_commit), "moderation")
        self.assertEqual(classify_commit_activity(code_commit), "code")
        self.assertEqual(classify_commit_activity(mixed_commit), "code")

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
            events = load_activity_events(self.repo_root, mode="all", limit=5)

        self.assertEqual([event.kind for event in events], ["moderation", "content"])
        self.assertEqual(events[0].moderation_record.record_id, "pin-root-001")
        self.assertEqual(events[1].commit.subject, "Add root-001")

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

        content_events = load_activity_events(self.repo_root, mode="content", limit=5)
        moderation_events = load_activity_events(self.repo_root, mode="moderation", limit=5)
        code_events = load_activity_events(self.repo_root, mode="code", limit=5)

        self.assertTrue(all(event.kind == "content" for event in content_events))
        self.assertTrue(all(event.kind == "moderation" for event in moderation_events))
        self.assertEqual(code_events, [])

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
        self.assertIn("forum_web_stub.py", commits[0].files)
        self.assertEqual(classify_commit_activity(commits[0]), "code")


if __name__ == "__main__":
    unittest.main()
