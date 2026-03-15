from __future__ import annotations

import unittest
from pathlib import Path
from textwrap import dedent

from forum_read_only.repository import is_task_root, parse_post_text, root_thread_type


class ThreadTypedRootParsingTests(unittest.TestCase):
    def test_parse_plain_root_without_thread_type(self) -> None:
        post = parse_post_text(
            dedent(
                """
                Post-ID: root-001
                Board-Tags: general
                Subject: Plain root

                Ordinary thread body.
                """
            ).lstrip(),
            source_path=Path("records/posts/root-001.txt"),
        )

        self.assertTrue(post.is_root)
        self.assertIsNone(root_thread_type(post))
        self.assertFalse(is_task_root(post))
        self.assertIsNone(post.task_metadata)

    def test_parse_task_root_metadata(self) -> None:
        post = parse_post_text(
            dedent(
                """
                Post-ID: T01
                Board-Tags: planning
                Subject: Example task
                Thread-Type: task
                Task-Status: proposed
                Task-Presentability-Impact: 0.75
                Task-Implementation-Difficulty: 0.25
                Task-Depends-On: T00
                Task-Sources: todo.txt; ideas.txt

                Example task summary.
                """
            ).lstrip(),
            source_path=Path("records/posts/T01.txt"),
        )

        self.assertEqual(root_thread_type(post), "task")
        self.assertTrue(is_task_root(post))
        assert post.task_metadata is not None
        self.assertEqual(post.task_metadata.status, "proposed")
        self.assertEqual(post.task_metadata.presentability_impact, 0.75)
        self.assertEqual(post.task_metadata.implementation_difficulty, 0.25)
        self.assertEqual(post.task_metadata.dependencies, ("T00",))
        self.assertEqual(post.task_metadata.sources, ("todo.txt", "ideas.txt"))

    def test_reject_task_headers_on_reply(self) -> None:
        with self.assertRaisesRegex(ValueError, "Task-\\* headers are only valid on task root threads"):
            parse_post_text(
                dedent(
                    """
                    Post-ID: reply-001
                    Board-Tags: planning
                    Thread-ID: T01
                    Parent-ID: T01
                    Task-Status: proposed

                    Reply body.
                    """
                ).lstrip(),
            )

    def test_parse_placeholder_non_task_typed_root(self) -> None:
        post = parse_post_text(
            dedent(
                """
                Post-ID: proposal-001
                Board-Tags: planning
                Subject: Future proposal
                Thread-Type: proposal

                Placeholder typed root.
                """
            ).lstrip(),
        )

        self.assertEqual(root_thread_type(post), "proposal")
        self.assertFalse(is_task_root(post))
        self.assertIsNone(post.task_metadata)


if __name__ == "__main__":
    unittest.main()
