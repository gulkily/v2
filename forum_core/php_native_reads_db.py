from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def php_native_reads_db_path(repo_root: Path) -> Path:
    return repo_root / "state" / "cache" / "php_native_reads.sqlite3"


def connect_php_native_reads_db(repo_root: Path) -> sqlite3.Connection:
    db_path = php_native_reads_db_path(repo_root)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    ensure_php_native_snapshots_schema(connection)
    return connection


def ensure_php_native_snapshots_schema(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS php_native_snapshots (
            snapshot_id TEXT PRIMARY KEY,
            entity_type TEXT NOT NULL,
            entity_id TEXT,
            snapshot_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            refreshed_at TEXT NOT NULL,
            invalidated_by_post_id TEXT,
            entity_version TEXT
        )
        """
    )
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS snapshots_entity_type_id
        ON php_native_snapshots(entity_type, entity_id)
        """
    )
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS snapshots_refreshed_at
        ON php_native_snapshots(refreshed_at)
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS php_native_read_counters (
            route_path TEXT NOT NULL,
            user_type TEXT NOT NULL,
            outcome TEXT NOT NULL,
            count INTEGER NOT NULL DEFAULT 0,
            updated_at TEXT NOT NULL,
            PRIMARY KEY (route_path, user_type, outcome)
        )
        """
    )
    connection.commit()


def _utc_now_text() -> str:
    return datetime.now(timezone.utc).isoformat()


def save_php_native_snapshot(
    connection: sqlite3.Connection,
    *,
    snapshot_id: str,
    entity_type: str,
    entity_id: str | None,
    snapshot: dict[str, Any],
    invalidated_by_post_id: str | None = None,
    entity_version: str | None = None,
) -> None:
    now_text = _utc_now_text()
    row = connection.execute(
        "SELECT created_at FROM php_native_snapshots WHERE snapshot_id = ?",
        (snapshot_id,),
    ).fetchone()
    created_at = row[0] if row is not None else now_text
    connection.execute(
        """
        INSERT OR REPLACE INTO php_native_snapshots
        (snapshot_id, entity_type, entity_id, snapshot_json, created_at, refreshed_at, invalidated_by_post_id, entity_version)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            snapshot_id,
            entity_type,
            entity_id,
            json.dumps(snapshot, indent=2, sort_keys=True),
            created_at,
            now_text,
            invalidated_by_post_id,
            entity_version,
        ),
    )
    connection.commit()


def load_php_native_snapshot(connection: sqlite3.Connection, snapshot_id: str) -> dict[str, Any] | None:
    row = connection.execute(
        "SELECT snapshot_json FROM php_native_snapshots WHERE snapshot_id = ?",
        (snapshot_id,),
    ).fetchone()
    if row is None:
        return None
    loaded = json.loads(row[0])
    return loaded if isinstance(loaded, dict) else None


def delete_php_native_snapshot(connection: sqlite3.Connection, snapshot_id: str) -> None:
    connection.execute(
        "DELETE FROM php_native_snapshots WHERE snapshot_id = ?",
        (snapshot_id,),
    )
    connection.commit()


def list_snapshots_by_type(connection: sqlite3.Connection, entity_type: str) -> list[str]:
    rows = connection.execute(
        "SELECT snapshot_id FROM php_native_snapshots WHERE entity_type = ? ORDER BY snapshot_id",
        (entity_type,),
    ).fetchall()
    return [str(row[0]) for row in rows]


def increment_php_native_read_counter(
    connection: sqlite3.Connection,
    *,
    route_path: str,
    user_type: str,
    outcome: str,
) -> None:
    now_text = _utc_now_text()
    connection.execute(
        """
        INSERT INTO php_native_read_counters(route_path, user_type, outcome, count, updated_at)
        VALUES (?, ?, ?, 1, ?)
        ON CONFLICT(route_path, user_type, outcome)
        DO UPDATE SET count = count + 1, updated_at = excluded.updated_at
        """,
        (route_path, user_type, outcome, now_text),
    )
    connection.commit()
