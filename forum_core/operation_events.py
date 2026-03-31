from __future__ import annotations

import json
import os
import sqlite3
import time
import uuid
from contextlib import contextmanager
from contextvars import ContextVar, Token
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterator


_CURRENT_OPERATION: ContextVar["OperationHandle | None"] = ContextVar("current_operation", default=None)


@dataclass(frozen=True)
class OperationStep:
    name: str
    duration_ms: float


@dataclass(frozen=True)
class OperationEvent:
    operation_id: str
    operation_kind: str
    operation_name: str
    state: str
    started_at: str
    updated_at: str
    ended_at: str | None
    total_duration_ms: float | None
    error_text: str | None
    metadata: dict[str, str]
    steps: tuple[OperationStep, ...]


@dataclass(frozen=True)
class OperationHandle:
    repo_root: Path
    operation_id: str
    operation_kind: str
    operation_name: str
    started_at_monotonic: float


def operation_events_path(repo_root: Path) -> Path:
    return repo_root / "state" / "cache" / "operation_events.sqlite3"


def operation_event_retention_hours(env: dict[str, str] | None = None) -> int:
    source_env = os.environ if env is None else env
    raw_value = source_env.get("FORUM_OPERATION_EVENT_RETENTION_HOURS", "6").strip()
    try:
        retention_hours = int(raw_value)
    except ValueError:
        return 6
    return retention_hours if retention_hours > 0 else 6


def _connect(repo_root: Path) -> sqlite3.Connection:
    path = operation_events_path(repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode = WAL")
    ensure_operation_events_schema(connection)
    return connection


def ensure_operation_events_schema(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS operation_events (
            operation_id TEXT PRIMARY KEY,
            operation_kind TEXT NOT NULL,
            operation_name TEXT NOT NULL,
            state TEXT NOT NULL,
            started_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            ended_at TEXT,
            total_duration_ms REAL,
            error_text TEXT,
            metadata_json TEXT NOT NULL,
            steps_json TEXT NOT NULL
        )
        """
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS operation_events_started_at_idx ON operation_events(started_at DESC)"
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS operation_events_state_idx ON operation_events(state)"
    )
    connection.commit()


def _utc_now_text() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _normalize_metadata(metadata: dict[str, object] | None) -> dict[str, str]:
    if not metadata:
        return {}
    return {str(key): str(value) for key, value in metadata.items()}


def _cleanup_expired_events(connection: sqlite3.Connection, *, retention_hours: int) -> None:
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=retention_hours)).isoformat().replace("+00:00", "Z")
    connection.execute(
        """
        DELETE FROM operation_events
        WHERE ended_at IS NOT NULL
          AND ended_at < ?
        """,
        (cutoff,),
    )


def start_operation(
    repo_root: Path,
    *,
    operation_kind: str,
    operation_name: str,
    metadata: dict[str, str] | None = None,
) -> OperationHandle:
    started_at = _utc_now_text()
    handle = OperationHandle(
        repo_root=repo_root,
        operation_id=str(uuid.uuid4()),
        operation_kind=operation_kind,
        operation_name=operation_name,
        started_at_monotonic=time.perf_counter(),
    )
    with _connect(repo_root) as connection:
        _cleanup_expired_events(connection, retention_hours=operation_event_retention_hours())
        connection.execute(
            """
            INSERT INTO operation_events (
                operation_id,
                operation_kind,
                operation_name,
                state,
                started_at,
                updated_at,
                ended_at,
                total_duration_ms,
                error_text,
                metadata_json,
                steps_json
            )
            VALUES (?, ?, ?, ?, ?, ?, NULL, NULL, NULL, ?, ?)
            """,
            (
                handle.operation_id,
                operation_kind,
                operation_name,
                "running",
                started_at,
                started_at,
                json.dumps(_normalize_metadata(metadata), sort_keys=True),
                "[]",
            ),
        )
        connection.commit()
    return handle


def _load_steps(connection: sqlite3.Connection, *, operation_id: str) -> list[dict[str, object]]:
    row = connection.execute(
        "SELECT steps_json FROM operation_events WHERE operation_id = ?",
        (operation_id,),
    ).fetchone()
    if row is None:
        return []
    return list(json.loads(row["steps_json"]))


def _update_steps(handle: OperationHandle, steps: list[dict[str, object]]) -> None:
    with _connect(handle.repo_root) as connection:
        connection.execute(
            """
            UPDATE operation_events
            SET steps_json = ?, updated_at = ?
            WHERE operation_id = ?
            """,
            (
                json.dumps(steps, sort_keys=True),
                _utc_now_text(),
                handle.operation_id,
            ),
        )
        connection.commit()


def record_operation_step(handle: OperationHandle, *, name: str, duration_ms: float) -> None:
    with _connect(handle.repo_root) as connection:
        steps = _load_steps(connection, operation_id=handle.operation_id)
        steps.append(
            {
                "duration_ms": round(duration_ms, 2),
                "name": name,
            }
        )
        connection.execute(
            """
            UPDATE operation_events
            SET steps_json = ?, updated_at = ?
            WHERE operation_id = ?
            """,
            (
                json.dumps(steps, sort_keys=True),
                _utc_now_text(),
                handle.operation_id,
            ),
        )
        connection.commit()


def complete_operation(handle: OperationHandle) -> None:
    ended_at = _utc_now_text()
    total_duration_ms = round((time.perf_counter() - handle.started_at_monotonic) * 1000.0, 2)
    with _connect(handle.repo_root) as connection:
        connection.execute(
            """
            UPDATE operation_events
            SET state = ?, updated_at = ?, ended_at = ?, total_duration_ms = ?
            WHERE operation_id = ?
            """,
            (
                "completed",
                ended_at,
                ended_at,
                total_duration_ms,
                handle.operation_id,
            ),
        )
        connection.commit()


def fail_operation(handle: OperationHandle, *, error_text: str) -> None:
    ended_at = _utc_now_text()
    total_duration_ms = round((time.perf_counter() - handle.started_at_monotonic) * 1000.0, 2)
    with _connect(handle.repo_root) as connection:
        connection.execute(
            """
            UPDATE operation_events
            SET state = ?, updated_at = ?, ended_at = ?, total_duration_ms = ?, error_text = ?
            WHERE operation_id = ?
            """,
            (
                "failed",
                ended_at,
                ended_at,
                total_duration_ms,
                error_text,
                handle.operation_id,
            ),
        )
        connection.commit()


def current_operation() -> OperationHandle | None:
    return _CURRENT_OPERATION.get()


@contextmanager
def bind_operation(handle: OperationHandle) -> Iterator[OperationHandle]:
    token: Token[OperationHandle | None] = _CURRENT_OPERATION.set(handle)
    try:
        yield handle
    finally:
        _CURRENT_OPERATION.reset(token)


@contextmanager
def tracked_operation(
    repo_root: Path,
    *,
    operation_kind: str,
    operation_name: str,
    metadata: dict[str, str] | None = None,
) -> Iterator[OperationHandle | None]:
    existing = current_operation()
    if existing is not None:
        yield None
        return
    handle = start_operation(
        repo_root,
        operation_kind=operation_kind,
        operation_name=operation_name,
        metadata=metadata,
    )
    with bind_operation(handle):
        try:
            yield handle
        except Exception as exc:
            fail_operation(handle, error_text=str(exc))
            raise
        complete_operation(handle)


def record_current_operation_step(name: str, duration_ms: float) -> None:
    handle = current_operation()
    if handle is None:
        return
    record_operation_step(handle, name=name, duration_ms=duration_ms)


def emit_operation_timing(timing_callback, phase_name: str, duration_ms: float) -> None:
    if timing_callback is not None:
        timing_callback(phase_name, duration_ms)
    record_current_operation_step(phase_name, duration_ms)


def load_recent_operations(repo_root: Path, *, limit: int = 20) -> tuple[OperationEvent, ...]:
    with _connect(repo_root) as connection:
        rows = connection.execute(
            """
            SELECT operation_id, operation_kind, operation_name, state, started_at, updated_at,
                   ended_at, total_duration_ms, error_text, metadata_json, steps_json
            FROM operation_events
            ORDER BY
                CASE WHEN total_duration_ms IS NULL THEN -1 ELSE total_duration_ms END DESC,
                started_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return tuple(_row_to_operation_event(row) for row in rows)


def load_recent_slow_operations(
    repo_root: Path,
    *,
    limit: int = 20,
    min_duration_ms: float = 2000.0,
) -> tuple[OperationEvent, ...]:
    with _connect(repo_root) as connection:
        rows = connection.execute(
            """
            SELECT operation_id, operation_kind, operation_name, state, started_at, updated_at,
                   ended_at, total_duration_ms, error_text, metadata_json, steps_json
            FROM operation_events
            WHERE total_duration_ms > ?
            ORDER BY started_at DESC
            LIMIT ?
            """,
            (float(min_duration_ms), limit),
        ).fetchall()
    return tuple(_row_to_operation_event(row) for row in rows)


def _row_to_operation_event(row: sqlite3.Row) -> OperationEvent:
    steps = json.loads(row["steps_json"])
    metadata = _normalize_metadata(json.loads(row["metadata_json"]))
    return OperationEvent(
        operation_id=row["operation_id"],
        operation_kind=row["operation_kind"],
        operation_name=row["operation_name"],
        state=row["state"],
        started_at=row["started_at"],
        updated_at=row["updated_at"],
        ended_at=row["ended_at"],
        total_duration_ms=row["total_duration_ms"],
        error_text=row["error_text"],
        metadata=metadata,
        steps=tuple(OperationStep(name=step["name"], duration_ms=float(step["duration_ms"])) for step in steps),
    )
