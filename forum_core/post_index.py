from __future__ import annotations

import sqlite3
import subprocess
from dataclasses import dataclass
from pathlib import Path

from forum_core.identity import normalize_fingerprint, short_identity_label
from forum_core.merge_requests import derive_approved_merge_links
from forum_web.repository import Post, load_posts
from forum_web.profiles import (
    IdentityContext,
    load_identity_context,
    resolve_identity_display_name,
    username_route_token,
)


POST_INDEX_SCHEMA_VERSION = 3


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
    author_id: str | None = None


@dataclass(frozen=True)
class IndexedAuthorRow:
    author_id: str
    canonical_identity_id: str | None
    display_name: str
    display_name_source: str
    signer_fingerprint: str | None


@dataclass(frozen=True)
class IndexedIdentityMemberRow:
    canonical_identity_id: str
    member_identity_id: str


@dataclass(frozen=True)
class IndexedMergeEdgeRow:
    source_identity_id: str
    target_identity_id: str
    record_id: str
    timestamp: str
    edge_kind: str


@dataclass(frozen=True)
class IndexedUsernameClaimRow:
    canonical_identity_id: str
    source_identity_id: str
    display_name: str
    username_token: str
    claim_record_id: str
    claim_commit_id: str | None
    claim_commit_rank: int | None


@dataclass(frozen=True)
class IndexedUsernameRootRow:
    username_token: str
    canonical_identity_id: str
    display_name: str
    claim_record_id: str
    source_identity_id: str
    claim_commit_id: str | None
    claim_commit_rank: int | None


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
            updated_at TEXT,
            author_id TEXT
        );

        CREATE TABLE IF NOT EXISTS authors (
            author_id TEXT PRIMARY KEY,
            canonical_identity_id TEXT,
            display_name TEXT NOT NULL,
            display_name_source TEXT NOT NULL,
            signer_fingerprint TEXT
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

        CREATE TABLE IF NOT EXISTS identity_members (
            canonical_identity_id TEXT NOT NULL,
            member_identity_id TEXT NOT NULL PRIMARY KEY
        );

        CREATE TABLE IF NOT EXISTS active_merge_edges (
            source_identity_id TEXT NOT NULL,
            target_identity_id TEXT NOT NULL,
            record_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            edge_kind TEXT NOT NULL,
            PRIMARY KEY (source_identity_id, target_identity_id)
        );

        CREATE TABLE IF NOT EXISTS current_username_claims (
            canonical_identity_id TEXT PRIMARY KEY,
            source_identity_id TEXT NOT NULL,
            display_name TEXT NOT NULL,
            username_token TEXT NOT NULL,
            claim_record_id TEXT NOT NULL,
            claim_commit_id TEXT,
            claim_commit_rank INTEGER
        );

        CREATE TABLE IF NOT EXISTS username_roots (
            username_token TEXT PRIMARY KEY,
            canonical_identity_id TEXT NOT NULL,
            display_name TEXT NOT NULL,
            claim_record_id TEXT NOT NULL,
            source_identity_id TEXT NOT NULL,
            claim_commit_id TEXT,
            claim_commit_rank INTEGER
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
        ("author_id", "TEXT"),
    )
    for column_name, column_type in required_columns:
        if column_name in existing_columns:
            continue
        connection.execute(f"ALTER TABLE posts ADD COLUMN {column_name} {column_type}")

    connection.execute("CREATE INDEX IF NOT EXISTS posts_updated_at_idx ON posts(updated_at)")
    connection.execute("CREATE INDEX IF NOT EXISTS posts_created_at_idx ON posts(created_at)")
    connection.execute("CREATE INDEX IF NOT EXISTS posts_author_id_idx ON posts(author_id)")
    connection.execute("CREATE INDEX IF NOT EXISTS authors_canonical_identity_idx ON authors(canonical_identity_id)")
    connection.execute(
        "CREATE INDEX IF NOT EXISTS identity_members_canonical_idx ON identity_members(canonical_identity_id)"
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS active_merge_edges_target_idx ON active_merge_edges(target_identity_id)"
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS current_username_claims_token_idx ON current_username_claims(username_token)"
    )
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


def index_schema_is_current(connection: sqlite3.Connection) -> bool:
    indexed_schema_version = get_index_metadata(connection, "indexed_schema_version")
    return indexed_schema_version == str(POST_INDEX_SCHEMA_VERSION)


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
    connection.execute("DELETE FROM authors")
    connection.execute("DELETE FROM identity_members")
    connection.execute("DELETE FROM active_merge_edges")
    connection.execute("DELETE FROM current_username_claims")
    connection.execute("DELETE FROM username_roots")


def repo_commit_order(repo_root: Path) -> dict[str, int]:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "rev-list", "--topo-order", "--reverse", "HEAD"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0:
        return {}
    return {
        commit_id: index
        for index, commit_id in enumerate(line.strip() for line in result.stdout.splitlines() if line.strip())
    }


def first_commit_for_path(repo_root: Path, relative_path: str) -> str | None:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "log", "--diff-filter=A", "--format=%H", "--", relative_path],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0:
        return None
    commit_ids = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    if not commit_ids:
        return None
    return commit_ids[0]


def upsert_identity_members(
    connection: sqlite3.Connection,
    *,
    identity_context: IdentityContext,
) -> None:
    for canonical_identity_id, member_identity_ids in identity_context.resolution.members_by_canonical_identity_id.items():
        connection.executemany(
            """
            INSERT INTO identity_members (canonical_identity_id, member_identity_id)
            VALUES (?, ?)
            ON CONFLICT(member_identity_id) DO UPDATE SET
                canonical_identity_id = excluded.canonical_identity_id
            """,
            [(canonical_identity_id, member_identity_id) for member_identity_id in member_identity_ids],
        )


def upsert_active_merge_edges(
    connection: sqlite3.Connection,
    *,
    identity_context: IdentityContext,
) -> None:
    for record in derive_approved_merge_links(identity_context.merge_request_states):
        connection.execute(
            """
            INSERT INTO active_merge_edges (
                source_identity_id,
                target_identity_id,
                record_id,
                timestamp,
                edge_kind
            ) VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(source_identity_id, target_identity_id) DO UPDATE SET
                record_id = excluded.record_id,
                timestamp = excluded.timestamp,
                edge_kind = excluded.edge_kind
            """,
            (
                record.source_identity_id,
                record.target_identity_id,
                record.record_id,
                record.timestamp,
                "approved_merge_request",
            ),
        )


def current_username_claim_rows(
    *,
    repo_root: Path,
    identity_context: IdentityContext,
    commit_order: dict[str, int],
) -> list[IndexedUsernameClaimRow]:
    claim_rows: list[IndexedUsernameClaimRow] = []
    for canonical_identity_id, member_identity_ids in identity_context.resolution.members_by_canonical_identity_id.items():
        resolved = identity_context.resolved_display_name(canonical_identity_id)
        if resolved is None:
            continue
        username_token = username_route_token(resolved.display_name)
        if not username_token:
            continue
        record_path = next(
            (
                record.path
                for record in identity_context.profile_update_records
                if record.record_id == resolved.record_id
            ),
            None,
        )
        relative_path = (
            str(record_path.relative_to(repo_root))
            if record_path is not None and record_path.is_absolute()
            else None
        )
        claim_commit_id = first_commit_for_path(repo_root, relative_path) if relative_path is not None else None
        claim_rows.append(
            IndexedUsernameClaimRow(
                canonical_identity_id=canonical_identity_id,
                source_identity_id=resolved.source_identity_id,
                display_name=resolved.display_name,
                username_token=username_token,
                claim_record_id=resolved.record_id,
                claim_commit_id=claim_commit_id,
                claim_commit_rank=commit_order.get(claim_commit_id) if claim_commit_id is not None else None,
            )
        )
    return sorted(
        claim_rows,
        key=lambda row: (
            row.username_token,
            row.claim_commit_rank if row.claim_commit_rank is not None else 10**12,
            row.claim_record_id,
        ),
    )


def upsert_current_username_claims(
    connection: sqlite3.Connection,
    *,
    claim_rows: list[IndexedUsernameClaimRow],
) -> None:
    for row in claim_rows:
        connection.execute(
            """
            INSERT INTO current_username_claims (
                canonical_identity_id,
                source_identity_id,
                display_name,
                username_token,
                claim_record_id,
                claim_commit_id,
                claim_commit_rank
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(canonical_identity_id) DO UPDATE SET
                source_identity_id = excluded.source_identity_id,
                display_name = excluded.display_name,
                username_token = excluded.username_token,
                claim_record_id = excluded.claim_record_id,
                claim_commit_id = excluded.claim_commit_id,
                claim_commit_rank = excluded.claim_commit_rank
            """,
            (
                row.canonical_identity_id,
                row.source_identity_id,
                row.display_name,
                row.username_token,
                row.claim_record_id,
                row.claim_commit_id,
                row.claim_commit_rank,
            ),
        )


def upsert_username_roots(
    connection: sqlite3.Connection,
    *,
    claim_rows: list[IndexedUsernameClaimRow],
) -> None:
    best_by_token: dict[str, IndexedUsernameClaimRow] = {}
    for row in claim_rows:
        previous = best_by_token.get(row.username_token)
        if previous is None:
            best_by_token[row.username_token] = row
            continue
        row_key = (
            row.claim_commit_rank if row.claim_commit_rank is not None else 10**12,
            row.claim_record_id,
        )
        previous_key = (
            previous.claim_commit_rank if previous.claim_commit_rank is not None else 10**12,
            previous.claim_record_id,
        )
        if row_key < previous_key:
            best_by_token[row.username_token] = row

    for username_token, row in sorted(best_by_token.items()):
        connection.execute(
            """
            INSERT INTO username_roots (
                username_token,
                canonical_identity_id,
                display_name,
                claim_record_id,
                source_identity_id,
                claim_commit_id,
                claim_commit_rank
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(username_token) DO UPDATE SET
                canonical_identity_id = excluded.canonical_identity_id,
                display_name = excluded.display_name,
                claim_record_id = excluded.claim_record_id,
                source_identity_id = excluded.source_identity_id,
                claim_commit_id = excluded.claim_commit_id,
                claim_commit_rank = excluded.claim_commit_rank
            """,
            (
                username_token,
                row.canonical_identity_id,
                row.display_name,
                row.claim_record_id,
                row.source_identity_id,
                row.claim_commit_id,
                row.claim_commit_rank,
            ),
        )


def author_id_for_post(post: Post, identity_context: IdentityContext | None) -> str | None:
    canonical_identity_id = None
    if identity_context is not None and post.identity_id is not None:
        canonical_identity_id = identity_context.canonical_identity_id(post.identity_id) or post.identity_id
    elif post.identity_id is not None:
        canonical_identity_id = post.identity_id
    if canonical_identity_id is not None:
        return canonical_identity_id
    if post.signer_fingerprint is not None:
        return f"fingerprint:{normalize_fingerprint(post.signer_fingerprint).lower()}"
    return None


def author_row_for_post(post: Post, *, identity_context: IdentityContext | None) -> IndexedAuthorRow | None:
    author_id = author_id_for_post(post, identity_context)
    if author_id is None:
        return None
    canonical_identity_id = None
    if identity_context is not None and post.identity_id is not None:
        canonical_identity_id = identity_context.canonical_identity_id(post.identity_id) or post.identity_id
    elif post.identity_id is not None:
        canonical_identity_id = post.identity_id

    if post.signer_fingerprint is not None:
        fallback_display_name = short_identity_label(post.signer_fingerprint)
    else:
        fallback_display_name = "Unknown author"

    display_name_source = "fingerprint_fallback"
    display_name = fallback_display_name
    if identity_context is not None and post.identity_id is not None:
        display_name = resolve_identity_display_name(
            identity_context=identity_context,
            identity_id=post.identity_id,
            fallback_display_name=fallback_display_name,
        )
        resolved_display_name = identity_context.resolved_display_name(post.identity_id)
        if resolved_display_name is not None:
            display_name_source = "profile_update"

    signer_fingerprint = (
        normalize_fingerprint(post.signer_fingerprint)
        if post.signer_fingerprint is not None
        else None
    )
    return IndexedAuthorRow(
        author_id=author_id,
        canonical_identity_id=canonical_identity_id,
        display_name=display_name,
        display_name_source=display_name_source,
        signer_fingerprint=signer_fingerprint,
    )


def upsert_indexed_author(connection: sqlite3.Connection, *, author: IndexedAuthorRow) -> None:
    connection.execute(
        """
        INSERT INTO authors (
            author_id,
            canonical_identity_id,
            display_name,
            display_name_source,
            signer_fingerprint
        ) VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(author_id) DO UPDATE SET
            canonical_identity_id = excluded.canonical_identity_id,
            display_name = excluded.display_name,
            display_name_source = excluded.display_name_source,
            signer_fingerprint = excluded.signer_fingerprint
        """,
        (
            author.author_id,
            author.canonical_identity_id,
            author.display_name,
            author.display_name_source,
            author.signer_fingerprint,
        ),
    )


def upsert_indexed_post(
    connection: sqlite3.Connection,
    *,
    post: Post,
    repo_root: Path,
    timestamps: PostCommitTimestamps,
    identity_context: IdentityContext | None = None,
) -> None:
    relative_path = str(post.path.relative_to(repo_root))
    task_status = None
    task_presentability_impact = None
    task_implementation_difficulty = None
    if post.task_metadata is not None:
        task_status = post.task_metadata.status
        task_presentability_impact = post.task_metadata.presentability_impact
        task_implementation_difficulty = post.task_metadata.implementation_difficulty
    author = author_row_for_post(post, identity_context=identity_context)
    if author is not None:
        upsert_indexed_author(connection, author=author)

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
            updated_at,
            author_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            updated_at = excluded.updated_at,
            author_id = excluded.author_id
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
            author.author_id if author is not None else None,
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
    identity_context = load_identity_context(repo_root=repo_root, posts=posts)
    timestamps_by_post_id = post_commit_timestamps(repo_root)
    commit_order = repo_commit_order(repo_root)
    clear_post_index(active_index.connection)
    for post in posts:
        upsert_indexed_post(
            active_index.connection,
            post=post,
            repo_root=repo_root,
            timestamps=timestamps_by_post_id.get(post.post_id, PostCommitTimestamps(created_at=None, updated_at=None)),
            identity_context=identity_context,
        )
    upsert_identity_members(active_index.connection, identity_context=identity_context)
    upsert_active_merge_edges(active_index.connection, identity_context=identity_context)
    claim_rows = current_username_claim_rows(
        repo_root=repo_root,
        identity_context=identity_context,
        commit_order=commit_order,
    )
    upsert_current_username_claims(active_index.connection, claim_rows=claim_rows)
    upsert_username_roots(active_index.connection, claim_rows=claim_rows)
    indexed_head = current_repo_head(repo_root)
    set_index_metadata(active_index.connection, "indexed_head", indexed_head or "")
    set_index_metadata(active_index.connection, "indexed_post_count", str(len(posts)))
    set_index_metadata(active_index.connection, "indexed_schema_version", str(POST_INDEX_SCHEMA_VERSION))
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
    if (
        indexed_count != expected_count
        or indexed_head != current_head
        or not index_schema_is_current(index.connection)
    ):
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
        if any(
            touched_path.startswith("records/profile-updates/")
            or touched_path.startswith("records/identity/")
            or touched_path.startswith("records/identity-links/")
            for touched_path in touched_paths
        ):
            rebuild_post_index(repo_root, index=index)
            set_index_metadata(index.connection, "indexed_head", commit_id)
            set_index_metadata(
                index.connection,
                "indexed_post_count",
                str(len(list(records_posts_dir(repo_root).glob("*.txt")))),
            )
            set_index_metadata(index.connection, "indexed_schema_version", str(POST_INDEX_SCHEMA_VERSION))
            index.connection.commit()
            return
        posts = load_posts(records_posts_dir(repo_root))
        identity_context = load_identity_context(repo_root=repo_root, posts=posts)
        posts_by_path = {candidate.path: candidate for candidate in posts}
        timestamps_by_post_id = post_commit_timestamps(repo_root)
        for touched_path in touched_paths:
            path = repo_root / touched_path
            if path.parent != records_posts_dir(repo_root) or path.suffix != ".txt":
                continue
            if not path.exists():
                continue
            matching_post = posts_by_path.get(path)
            if matching_post is None:
                continue
            timestamps = timestamps_by_post_id.get(
                matching_post.post_id,
                PostCommitTimestamps(created_at=None, updated_at=None),
            )
            upsert_indexed_post(
                index.connection,
                post=matching_post,
                repo_root=repo_root,
                timestamps=timestamps,
                identity_context=identity_context,
            )
        set_index_metadata(index.connection, "indexed_head", commit_id)
        set_index_metadata(
            index.connection,
            "indexed_post_count",
            str(len(list(records_posts_dir(repo_root).glob("*.txt")))),
        )
        set_index_metadata(index.connection, "indexed_schema_version", str(POST_INDEX_SCHEMA_VERSION))
        index.connection.commit()
    finally:
        index.connection.close()


def load_indexed_root_posts(repo_root: Path, *, board_tag: str | None = None) -> dict[str, IndexedPostRow]:
    index = ensure_post_index_current(repo_root)
    try:
        parameters: list[str] = []
        sql = """
            SELECT posts.post_id, posts.created_at, posts.updated_at, posts.author_id
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
                author_id=row["author_id"],
            )
            for row in rows
        }
    finally:
        index.connection.close()


def load_indexed_authors(repo_root: Path) -> dict[str, IndexedAuthorRow]:
    index = ensure_post_index_current(repo_root)
    try:
        rows = index.connection.execute(
            """
            SELECT author_id, canonical_identity_id, display_name, display_name_source, signer_fingerprint
            FROM authors
            """
        ).fetchall()
        return {
            row["author_id"]: IndexedAuthorRow(
                author_id=row["author_id"],
                canonical_identity_id=row["canonical_identity_id"],
                display_name=row["display_name"],
                display_name_source=row["display_name_source"],
                signer_fingerprint=row["signer_fingerprint"],
            )
            for row in rows
        }
    finally:
        index.connection.close()


def load_indexed_identity_members(repo_root: Path) -> dict[str, tuple[str, ...]]:
    index = ensure_post_index_current(repo_root)
    try:
        rows = index.connection.execute(
            """
            SELECT canonical_identity_id, member_identity_id
            FROM identity_members
            ORDER BY canonical_identity_id, member_identity_id
            """
        ).fetchall()
        members_by_canonical_identity_id: dict[str, list[str]] = {}
        for row in rows:
            members_by_canonical_identity_id.setdefault(row["canonical_identity_id"], []).append(row["member_identity_id"])
        return {
            canonical_identity_id: tuple(member_identity_ids)
            for canonical_identity_id, member_identity_ids in members_by_canonical_identity_id.items()
        }
    finally:
        index.connection.close()


def load_indexed_username_roots(repo_root: Path) -> dict[str, IndexedUsernameRootRow]:
    index = ensure_post_index_current(repo_root)
    try:
        rows = index.connection.execute(
            """
            SELECT username_token, canonical_identity_id, display_name, claim_record_id,
                   source_identity_id, claim_commit_id, claim_commit_rank
            FROM username_roots
            """
        ).fetchall()
        return {
            row["username_token"]: IndexedUsernameRootRow(
                username_token=row["username_token"],
                canonical_identity_id=row["canonical_identity_id"],
                display_name=row["display_name"],
                claim_record_id=row["claim_record_id"],
                source_identity_id=row["source_identity_id"],
                claim_commit_id=row["claim_commit_id"],
                claim_commit_rank=row["claim_commit_rank"],
            )
            for row in rows
        }
    finally:
        index.connection.close()


def load_indexed_username_claims(
    repo_root: Path,
    *,
    username_token: str | None = None,
) -> tuple[IndexedUsernameClaimRow, ...]:
    index = ensure_post_index_current(repo_root)
    try:
        sql = """
            SELECT canonical_identity_id, source_identity_id, display_name, username_token,
                   claim_record_id, claim_commit_id, claim_commit_rank
            FROM current_username_claims
        """
        parameters: list[str] = []
        if username_token is not None:
            sql += " WHERE username_token = ?"
            parameters.append(username_token)
        sql += " ORDER BY username_token, claim_commit_rank, claim_record_id, canonical_identity_id"
        rows = index.connection.execute(sql, parameters).fetchall()
        return tuple(
            IndexedUsernameClaimRow(
                canonical_identity_id=row["canonical_identity_id"],
                source_identity_id=row["source_identity_id"],
                display_name=row["display_name"],
                username_token=row["username_token"],
                claim_record_id=row["claim_record_id"],
                claim_commit_id=row["claim_commit_id"],
                claim_commit_rank=row["claim_commit_rank"],
            )
            for row in rows
        )
    finally:
        index.connection.close()
