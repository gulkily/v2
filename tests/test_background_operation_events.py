from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from forum_core.operation_events import load_recent_operations
from forum_core.post_index import ensure_post_index_current, rebuild_post_index


class BackgroundOperationEventsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.tempdir.name)
        (self.repo_root / "records" / "posts").mkdir(parents=True, exist_ok=True)
        (self.repo_root / "records" / "posts" / "root-001.txt").write_text(
            "Post-ID: root-001\nBoard-Tags: general\nSubject: Hello\n\nBody.\n",
            encoding="ascii",
        )
        subprocess.run(["git", "init"], cwd=self.repo_root, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=self.repo_root, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=self.repo_root, check=True)
        subprocess.run(["git", "add", "."], cwd=self.repo_root, check=True)
        subprocess.run(["git", "commit", "-m", "initial"], cwd=self.repo_root, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_ensure_post_index_current_records_startup_operation_outside_request_context(self) -> None:
        ensure_post_index_current(self.repo_root).connection.close()

        operations = load_recent_operations(self.repo_root)
        event = next(operation for operation in operations if operation.operation_name == "post_index_ready_check")
        self.assertEqual(event.state, "completed")
        self.assertEqual(event.operation_kind, "startup")

    def test_rebuild_post_index_is_visible_while_running(self) -> None:
        original_load_posts = rebuild_post_index.__globals__["load_posts"]

        def delayed_load_posts(records_dir: Path):
            operations = load_recent_operations(self.repo_root)
            running = next(operation for operation in operations if operation.operation_name == "post_index_rebuild")
            self.assertEqual(running.state, "running")
            return original_load_posts(records_dir)

        with mock.patch("forum_core.post_index.load_posts", side_effect=delayed_load_posts):
            rebuild_post_index(self.repo_root)

        operations = load_recent_operations(self.repo_root)
        event = next(operation for operation in operations if operation.operation_name == "post_index_rebuild")
        self.assertEqual(event.state, "completed")
        self.assertIn("post_index_load_posts", tuple(step.name for step in event.steps))

    def test_rebuild_post_index_records_detailed_timestamp_substeps(self) -> None:
        rebuild_post_index(self.repo_root)

        operations = load_recent_operations(self.repo_root)
        event = next(operation for operation in operations if operation.operation_name == "post_index_rebuild")
        step_names = tuple(step.name for step in event.steps)

        self.assertIn("post_index_commit_timestamp_paths", step_names)
        self.assertIn("post_index_commit_timestamp_git_logs", step_names)
        self.assertIn("post_index_commit_timestamps", step_names)


if __name__ == "__main__":
    unittest.main()
