from __future__ import annotations

import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

from forum_core.operation_events import (
    bind_operation,
    complete_operation,
    current_operation,
    fail_operation,
    load_recent_operations,
    load_recent_slow_operations,
    operation_events_path,
    record_current_operation_step,
    start_operation,
)


class OperationEventsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.tempdir.name)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_operation_lifecycle_persists_steps_and_completion(self) -> None:
        handle = start_operation(
            self.repo_root,
            operation_kind="request",
            operation_name="GET /instance/",
            metadata={"path": "/instance/"},
        )

        with bind_operation(handle):
            self.assertIsNotNone(current_operation())
            record_current_operation_step("load_instance_info", 12.5)
            record_current_operation_step("render_page", 3.25)

        complete_operation(handle)

        operations = load_recent_operations(self.repo_root)
        self.assertEqual(len(operations), 1)
        event = operations[0]
        self.assertEqual(event.state, "completed")
        self.assertEqual(event.operation_kind, "request")
        self.assertEqual(event.operation_name, "GET /instance/")
        self.assertEqual(event.metadata["path"], "/instance/")
        self.assertEqual(tuple(step.name for step in event.steps), ("load_instance_info", "render_page"))
        self.assertIsNotNone(event.total_duration_ms)
        self.assertTrue(operation_events_path(self.repo_root).exists())

    def test_failed_operation_is_retained_with_error_text(self) -> None:
        handle = start_operation(
            self.repo_root,
            operation_kind="task",
            operation_name="post_index_rebuild",
        )

        fail_operation(handle, error_text="rebuild failed")

        operations = load_recent_operations(self.repo_root)
        self.assertEqual(operations[0].state, "failed")
        self.assertEqual(operations[0].error_text, "rebuild failed")

    def test_completed_operations_are_pruned_after_retention_window(self) -> None:
        older_time = "2000-01-01T00:00:00Z"
        handle = start_operation(
            self.repo_root,
            operation_kind="request",
            operation_name="GET /old",
        )
        complete_operation(handle)

        connection_path = operation_events_path(self.repo_root)
        import sqlite3

        connection = sqlite3.connect(connection_path)
        try:
            connection.execute(
                "UPDATE operation_events SET started_at = ?, updated_at = ?, ended_at = ?",
                (older_time, older_time, older_time),
            )
            connection.commit()
        finally:
            connection.close()

        with mock.patch.dict("os.environ", {"FORUM_OPERATION_EVENT_RETENTION_HOURS": "1"}, clear=False):
            start_operation(
                self.repo_root,
                operation_kind="request",
                operation_name="GET /new",
            )

        operations = load_recent_operations(self.repo_root)
        self.assertEqual(len(operations), 1)
        self.assertEqual(operations[0].operation_name, "GET /new")

    def test_load_recent_slow_operations_filters_by_threshold_and_recency(self) -> None:
        first = start_operation(
            self.repo_root,
            operation_kind="request",
            operation_name="GET /older-slow",
        )
        complete_operation(first)
        second = start_operation(
            self.repo_root,
            operation_kind="request",
            operation_name="GET /recent-fast",
        )
        complete_operation(second)
        third = start_operation(
            self.repo_root,
            operation_kind="request",
            operation_name="GET /recent-slow",
        )
        complete_operation(third)

        import sqlite3

        connection = sqlite3.connect(operation_events_path(self.repo_root))
        try:
            connection.execute(
                "UPDATE operation_events SET total_duration_ms = ?, started_at = ?, updated_at = ?, ended_at = ? WHERE operation_id = ?",
                (2500.0, "2026-03-18T10:00:00Z", "2026-03-18T10:00:01Z", "2026-03-18T10:00:02Z", first.operation_id),
            )
            connection.execute(
                "UPDATE operation_events SET total_duration_ms = ?, started_at = ?, updated_at = ?, ended_at = ? WHERE operation_id = ?",
                (1200.0, "2026-03-19T10:00:00Z", "2026-03-19T10:00:01Z", "2026-03-19T10:00:02Z", second.operation_id),
            )
            connection.execute(
                "UPDATE operation_events SET total_duration_ms = ?, started_at = ?, updated_at = ?, ended_at = ? WHERE operation_id = ?",
                (2600.0, "2026-03-19T12:00:00Z", "2026-03-19T12:00:01Z", "2026-03-19T12:00:02Z", third.operation_id),
            )
            connection.commit()
        finally:
            connection.close()

        operations = load_recent_slow_operations(self.repo_root, limit=10, min_duration_ms=2000.0)

        self.assertEqual(
            tuple(operation.operation_name for operation in operations),
            ("GET /recent-slow", "GET /older-slow"),
        )


if __name__ == "__main__":
    unittest.main()
