from __future__ import annotations

import sqlite3
import subprocess
from dataclasses import dataclass
from pathlib import Path

from forum_web.repository import Post, load_posts


POST_INDEX_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class PostIndex:
    path: Path
    connection: sqlite3.Connection


@dataclass(frozen=True)
class PostCommitTimestamps:
    created_at: str | None
    updated_at: str | None


@dataclass(frozen=True)
class IndexBuildResult:
    post_count: int
    indexed_head: str | None


@dataclass(frozen=True)
class IndexedPostRow:
    post_id: str
    created_at: str | None
    updated_at: str | None


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

        CREATE TABLE IF NOT EXISTS post_index_metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
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


def records_posts_dir(repo_root: Path) -> Path:
    return repo_root / "records" / "posts"


def get_index_metadata(connection: sqlite3.Connection, key: str) -> str | None:
    row = connection.execute(
        "SELECT value FROM post_index_metadata WHERE key = ?",
        (key,),
    ).fetchone()
    if row is None:
        return None
    return str(row["value"])


def set_index_metadata(connection: sqlite3.Connection, key: str, value: str) -> None:
    connection.execute(
        """
        INSERT INTO post_index_metadata (key, value)
        VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """,
        (key, value),
    )


def current_repo_head(repo_root: Path) -> str | None:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def post_commit_timestamps(repo_root: Path) -> dict[str, PostCommitTimestamps]:
    timestamps: dict[str, PostCommitTimestamps] = {}
    for path in sorted(records_posts_dir(repo_root).glob("*.txt")):
        relative_path = str(path.relative_to(repo_root))
        result = subprocess.run(
            ["git", "-C", str(repo_root), "log", "--follow", "--format=%cI", "--", relative_path],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        commit_times = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        if not commit_times:
            timestamps[path.stem] = PostCommitTimestamps(created_at=None, updated_at=None)
            continue
        timestamps[path.stem] = PostCommitTimestamps(
            created_at=commit_times[-1],
            updated_at=commit_times[0],
        )
    return timestamps


def clear_post_index(connection: sqlite3.Connection) -> None:
    connection.execute("DELETE FROM post_task_sources")
    connection.execute("DELETE FROM post_task_dependencies")
    connection.execute("DELETE FROM post_board_tags")
    connection.execute("DELETE FROM posts")


def upsert_indexed_post(
    connection: sqlite3.Connection,
    *,
    post: Post,
    repo_root: Path,
    timestamps: PostCommitTimestamps,
) -> None:
    relative_path = str(post.path.relative_to(repo_root))
    task_status = None
    task_presentability_impact = None
    task_implementation_difficulty = None
    if post.task_metadata is not None:
        task_status = post.task_metadata.status
        task_presentability_impact = post.task_metadata.presentability_impact
        task_implementation_difficulty = post.task_metadata.implementation_difficulty

    connection.execute(
        """
        INSERT INTO posts (
            post_id,
            relative_path,
            subject,
            thread_id,
            parent_id,
            root_thread_id,
            body,
            is_root,
            thread_type,
            signer_fingerprint,
            identity_id,
            proof_of_work,
            task_status,
            task_presentability_impact,
            task_implementation_difficulty,
            created_at,
            updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(post_id) DO UPDATE SET
            relative_path = excluded.relative_path,
            subject = excluded.subject,
            thread_id = excluded.thread_id,
            parent_id = excluded.parent_id,
            root_thread_id = excluded.root_thread_id,
            body = excluded.body,
            is_root = excluded.is_root,
            thread_type = excluded.thread_type,
            signer_fingerprint = excluded.signer_fingerprint,
            identity_id = excluded.identity_id,
            proof_of_work = excluded.proof_of_work,
            task_status = excluded.task_status,
            task_presentability_impact = excluded.task_presentability_impact,
            task_implementation_difficulty = excluded.task_implementation_difficulty,
            created_at = excluded.created_at,
            updated_at = excluded.updated_at
        """,
        (
            post.post_id,
            relative_path,
            post.subject,
            post.thread_id,
            post.parent_id,
            post.root_thread_id,
            post.body,
            1 if post.is_root else 0,
            post.thread_type,
            post.signer_fingerprint,
            post.identity_id,
            post.proof_of_work,
            task_status,
            task_presentability_impact,
            task_implementation_difficulty,
            timestamps.created_at,
            timestamps.updated_at,
        ),
    )
    connection.execute("DELETE FROM post_board_tags WHERE post_id = ?", (post.post_id,))
    connection.execute("DELETE FROM post_task_dependencies WHERE post_id = ?", (post.post_id,))
    connection.execute("DELETE FROM post_task_sources WHERE post_id = ?", (post.post_id,))
    connection.executemany(
        "INSERT INTO post_board_tags (post_id, board_tag) VALUES (?, ?)",
        [(post.post_id, tag) for tag in post.board_tags],
    )
    if post.task_metadata is not None:
        connection.executemany(
            "INSERT INTO post_task_dependencies (post_id, dependency_post_id) VALUES (?, ?)",
            [(post.post_id, dependency_post_id) for dependency_post_id in post.task_metadata.dependencies],
        )
        connection.executemany(
            "INSERT INTO post_task_sources (post_id, source_name) VALUES (?, ?)",
            [(post.post_id, source_name) for source_name in post.task_metadata.sources],
        )


def rebuild_post_index(repo_root: Path, index: PostIndex | None = None) -> IndexBuildResult:
    owned_index = index is None
    active_index = index or open_post_index(repo_root)
    posts = load_posts(records_posts_dir(repo_root))
    timestamps_by_post_id = post_commit_timestamps(repo_root)
    clear_post_index(active_index.connection)
    for post in posts:
        upsert_indexed_post(
            active_index.connection,
            post=post,
            repo_root=repo_root,
            timestamps=timestamps_by_post_id.get(post.post_id, PostCommitTimestamps(created_at=None, updated_at=None)),
        )
    indexed_head = current_repo_head(repo_root)
    set_index_metadata(active_index.connection, "indexed_head", indexed_head or "")
    set_index_metadata(active_index.connection, "indexed_post_count", str(len(posts)))
    active_index.connection.commit()
    if owned_index:
        active_index.connection.close()
    return IndexBuildResult(post_count=len(posts), indexed_head=indexed_head)


def ensure_post_index_current(repo_root: Path) -> PostIndex:
    index = open_post_index(repo_root)
    expected_count = len(list(records_posts_dir(repo_root).glob("*.txt")))
    indexed_head = get_index_metadata(index.connection, "indexed_head") or None
    indexed_count_text = get_index_metadata(index.connection, "indexed_post_count") or "0"
    try:
        indexed_count = int(indexed_count_text)
    except ValueError:
        indexed_count = -1
    current_head = current_repo_head(repo_root)
    if indexed_count != expected_count or indexed_head != current_head:
        rebuild_post_index(repo_root, index=index)
    return index


def refresh_post_index_after_commit(
    repo_root: Path,
    *,
    commit_id: str,
    touched_paths: tuple[str, ...],
) -> None:
    db_exists = post_index_path(repo_root).exists()
    if not db_exists:
        rebuild_post_index(repo_root)
        return

    index = open_post_index(repo_root)
    try:
        for touched_path in touched_paths:
            path = repo_root / touched_path
            if path.parent != records_posts_dir(repo_root) or path.suffix != ".txt":
                continue
            if not path.exists():
                continue
            post = load_posts(records_posts_dir(repo_root))
            matching_post = next((candidate for candidate in post if candidate.path == path), None)
            if matching_post is None:
                continue
            timestamps = post_commit_timestamps(repo_root).get(
                matching_post.post_id,
                PostCommitTimestamps(created_at=None, updated_at=None),
            )
            upsert_indexed_post(
                index.connection,
                post=matching_post,
                repo_root=repo_root,
                timestamps=timestamps,
            )
        set_index_metadata(index.connection, "indexed_head", commit_id)
        set_index_metadata(
            index.connection,
            "indexed_post_count",
            str(len(list(records_posts_dir(repo_root).glob("*.txt")))),
        )
        index.connection.commit()
    finally:
        index.connection.close()


def load_indexed_root_posts(repo_root: Path, *, board_tag: str | None = None) -> dict[str, IndexedPostRow]:
    index = ensure_post_index_current(repo_root)
    try:
        parameters: list[str] = []
        sql = """
            SELECT posts.post_id, posts.created_at, posts.updated_at
            FROM posts
            WHERE posts.is_root = 1
        """
        if board_tag is not None:
            sql += """
                AND EXISTS (
                    SELECT 1
                    FROM post_board_tags
                    WHERE post_board_tags.post_id = posts.post_id
                      AND post_board_tags.board_tag = ?
                )
            """
            parameters.append(board_tag)
        rows = index.connection.execute(sql, parameters).fetchall()
        return {
            row["post_id"]: IndexedPostRow(
                post_id=row["post_id"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            for row in rows
        }
    finally:
        index.connection.close()
