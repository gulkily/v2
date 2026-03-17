from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path


POST_INDEX_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class PostIndex:
    path: Path
    connection: sqlite3.Connection


def post_index_path(repo_root: Path) -> Path:
    return repo_root / "state" / "cache" / "post_index.sqlite3"


def open_post_index(repo_root: Path) -> PostIndex:
    path = post_index_path(repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    ensure_post_index_schema(connection)
    return PostIndex(path=path, connection=connection)


def current_post_index_schema_version(connection: sqlite3.Connection) -> int:
    row = connection.execute("PRAGMA user_version").fetchone()
    return int(row[0]) if row is not None else 0


def ensure_post_index_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS posts (
            post_id TEXT PRIMARY KEY,
            relative_path TEXT NOT NULL UNIQUE,
            subject TEXT NOT NULL,
            thread_id TEXT,
            parent_id TEXT,
            root_thread_id TEXT NOT NULL,
            body TEXT NOT NULL,
            is_root INTEGER NOT NULL,
            thread_type TEXT,
            signer_fingerprint TEXT,
            identity_id TEXT,
            proof_of_work TEXT,
            task_status TEXT,
            task_presentability_impact REAL,
            task_implementation_difficulty REAL,
            created_at TEXT,
            updated_at TEXT
        );

        CREATE TABLE IF NOT EXISTS post_board_tags (
            post_id TEXT NOT NULL,
            board_tag TEXT NOT NULL,
            PRIMARY KEY (post_id, board_tag),
            FOREIGN KEY (post_id) REFERENCES posts(post_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS post_task_dependencies (
            post_id TEXT NOT NULL,
            dependency_post_id TEXT NOT NULL,
            PRIMARY KEY (post_id, dependency_post_id),
            FOREIGN KEY (post_id) REFERENCES posts(post_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS post_task_sources (
            post_id TEXT NOT NULL,
            source_name TEXT NOT NULL,
            PRIMARY KEY (post_id, source_name),
            FOREIGN KEY (post_id) REFERENCES posts(post_id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS posts_root_thread_id_idx ON posts(root_thread_id);
        CREATE INDEX IF NOT EXISTS posts_is_root_idx ON posts(is_root);
        CREATE INDEX IF NOT EXISTS post_board_tags_tag_idx ON post_board_tags(board_tag);
        """
    )
    existing_columns = {
        row["name"]
        for row in connection.execute("PRAGMA table_info(posts)")
    }
    required_columns = (
        ("signer_fingerprint", "TEXT"),
        ("identity_id", "TEXT"),
        ("proof_of_work", "TEXT"),
        ("task_status", "TEXT"),
        ("task_presentability_impact", "REAL"),
        ("task_implementation_difficulty", "REAL"),
        ("created_at", "TEXT"),
        ("updated_at", "TEXT"),
    )
    for column_name, column_type in required_columns:
        if column_name in existing_columns:
            continue
        connection.execute(f"ALTER TABLE posts ADD COLUMN {column_name} {column_type}")

    connection.execute("CREATE INDEX IF NOT EXISTS posts_updated_at_idx ON posts(updated_at)")
    connection.execute("CREATE INDEX IF NOT EXISTS posts_created_at_idx ON posts(created_at)")
    current_version = current_post_index_schema_version(connection)
    if current_version < POST_INDEX_SCHEMA_VERSION:
        connection.execute(f"PRAGMA user_version = {POST_INDEX_SCHEMA_VERSION}")
    connection.commit()
