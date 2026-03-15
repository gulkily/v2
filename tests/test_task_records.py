from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from textwrap import dedent

from forum_read_only.tasks import load_tasks


class TaskRecordModelTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.tempdir.name)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def write_record(self, relative_path: str, raw_text: str) -> None:
        path = self.repo_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(dedent(raw_text).lstrip(), encoding="ascii")

    def test_load_tasks_parses_structured_fields(self) -> None:
        self.write_record(
            "records/tasks/task-t01.txt",
            """
            Task-ID: T01
            Title: Example task
            Status: proposed
            Presentability-Impact: 0.75
            Implementation-Difficulty: 0.25
            Discussion-Thread-ID: root-001
            Sources: todo.txt; ideas.txt

            Example summary body.
            """,
        )

        tasks = load_tasks(self.repo_root / "records" / "tasks")

        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].task_id, "T01")
        self.assertEqual(tasks[0].title, "Example task")
        self.assertEqual(tasks[0].status, "proposed")
        self.assertEqual(tasks[0].presentability_impact, 0.75)
        self.assertEqual(tasks[0].implementation_difficulty, 0.25)
        self.assertEqual(tasks[0].discussion_thread_id, "root-001")
        self.assertEqual(tasks[0].sources, ("todo.txt", "ideas.txt"))
        self.assertEqual(tasks[0].summary, "Example summary body.")

    def test_load_tasks_rejects_unknown_dependency(self) -> None:
        self.write_record(
            "records/tasks/task-t01.txt",
            """
            Task-ID: T01
            Title: Broken task
            Status: proposed
            Presentability-Impact: 0.40
            Implementation-Difficulty: 0.50
            Depends-On: T99
            Sources: todo.txt

            Broken dependency.
            """,
        )

        with self.assertRaisesRegex(ValueError, "unknown task T99"):
            load_tasks(self.repo_root / "records" / "tasks")

    def test_load_tasks_rejects_dependency_cycle(self) -> None:
        self.write_record(
            "records/tasks/task-t01.txt",
            """
            Task-ID: T01
            Title: Task one
            Status: proposed
            Presentability-Impact: 0.40
            Implementation-Difficulty: 0.50
            Depends-On: T02
            Sources: todo.txt

            First task.
            """,
        )
        self.write_record(
            "records/tasks/task-t02.txt",
            """
            Task-ID: T02
            Title: Task two
            Status: proposed
            Presentability-Impact: 0.60
            Implementation-Difficulty: 0.20
            Depends-On: T01
            Sources: ideas.txt

            Second task.
            """,
        )

        with self.assertRaisesRegex(ValueError, "cycle"):
            load_tasks(self.repo_root / "records" / "tasks")


if __name__ == "__main__":
    unittest.main()
