from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from forum_core.moderation import derive_moderation_state, load_moderation_records, moderation_records_dir, post_is_hidden, thread_is_hidden
from forum_core.post_index import IndexedPostRow, load_indexed_root_posts
from forum_core.thread_title_updates import load_thread_title_update_records, resolve_current_thread_title, thread_title_updates_dir
from forum_web.repository import group_threads, load_posts, root_thread_type


def php_native_reads_dir(repo_root: Path) -> Path:
    return repo_root / "state" / "cache" / "php_native_reads"


def post_records_dir(repo_root: Path) -> Path:
    return repo_root / "records" / "posts"


def board_index_snapshot_path(repo_root: Path) -> Path:
    return php_native_reads_dir(repo_root) / "board_index_root.json"


def _first_line(text: str) -> str:
    for line in text.splitlines():
        trimmed = line.strip()
        if trimmed:
            return trimmed
    return ""


def _indexed_timestamp_value(timestamp_text: str | None) -> float:
    if not timestamp_text:
        return float("-inf")
    try:
        return datetime.fromisoformat(timestamp_text).timestamp()
    except ValueError:
        return float("-inf")


def _indexed_thread_sort_key(thread, moderation_state, *, indexed_roots: dict[str, IndexedPostRow]):
    indexed_root = indexed_roots.get(thread.root.post_id)
    updated_at = _indexed_timestamp_value(indexed_root.updated_at if indexed_root is not None else None)
    created_at = _indexed_timestamp_value(indexed_root.created_at if indexed_root is not None else None)
    return (
        0 if moderation_state.pins_thread(thread.root.post_id) else 1,
        -updated_at,
        -created_at,
        thread.root.post_id,
    )


def _visible_reply_count(thread, moderation_state) -> int:
    return sum(
        0
        if post_is_hidden(moderation_state, reply.post_id, thread.root.post_id)
        else 1
        for reply in thread.replies
    )


def build_board_index_snapshot(repo_root: Path) -> dict[str, object]:
    posts = load_posts(post_records_dir(repo_root))
    threads = group_threads(posts)
    moderation_state = derive_moderation_state(load_moderation_records(moderation_records_dir(repo_root)))
    indexed_roots = load_indexed_root_posts(repo_root)
    title_updates = load_thread_title_update_records(thread_title_updates_dir(repo_root))
    public_threads = sorted(
        [
            thread
            for thread in threads
            if not thread_is_hidden(moderation_state, thread.root.post_id)
        ],
        key=lambda thread: _indexed_thread_sort_key(
            thread,
            moderation_state,
            indexed_roots=indexed_roots,
        ),
    )
    board_tags = sorted({tag for thread in public_threads for tag in thread.root.board_tags})
    thread_rows: list[dict[str, object]] = []
    for thread in public_threads:
        subject = resolve_current_thread_title(
            thread_id=thread.root.post_id,
            root_subject=thread.root.subject or "Untitled thread",
            updates=title_updates,
        )
        preview = _first_line(thread.root.body) or "No preview available."
        visible_tags = tuple(tag for tag in thread.root.board_tags if tag and tag != "general")
        thread_rows.append(
            {
                "post_id": thread.root.post_id,
                "thread_href": f"/threads/{thread.root.post_id}",
                "subject": subject,
                "preview": preview,
                "tags": list(visible_tags),
                "reply_count": _visible_reply_count(thread, moderation_state),
                "thread_type": root_thread_type(thread.root),
            }
        )
    return {
        "route": "/",
        "thread_rows": thread_rows,
        "stats": {
            "post_count": len(posts),
            "thread_count": len(public_threads),
            "board_tag_count": len(board_tags),
        },
    }


def refresh_php_native_read_artifacts(repo_root: Path) -> None:
    snapshot_path = board_index_snapshot_path(repo_root)
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot_path.write_text(
        json.dumps(build_board_index_snapshot(repo_root), indent=2, sort_keys=True),
        encoding="utf-8",
    )
