from __future__ import annotations

from forum_core.moderation import ModerationRecord
from forum_core.identity import ProfileSummary, render_profile_summary_text
from forum_read_only.repository import Post, Thread, is_task_root, root_thread_type


def render_api_home_text(*, post_count: int, thread_count: int, board_tags: list[str]) -> str:
    lines = [
        "FORUM-API/1",
        "Mode: mixed",
        "Available-Commands: list_index get_thread get_post get_profile get_moderation_log create_thread create_reply moderate link_identity update_profile",
        f"Post-Count: {post_count}",
        f"Thread-Count: {thread_count}",
        f"Board-Tags: {' '.join(board_tags)}",
        "",
        "Routes:",
        "/api/",
        "/api/create_thread",
        "/api/create_reply",
        "/api/moderate",
        "/api/link_identity",
        "/api/update_profile",
        "/api/list_index",
        "/api/get_thread?thread_id=<thread-id>",
        "/api/get_post?post_id=<post-id>",
        "/api/get_profile?identity_id=<identity-id>",
        "/api/get_moderation_log?limit=<decimal>&before=<record-id-or-empty>",
    ]
    return "\n".join(lines) + "\n"


def render_index_text(
    threads: list[Thread],
    *,
    board_tag: str | None = None,
    visible_reply_counts: dict[str, int] | None = None,
    pinned_thread_ids: frozenset[str] | None = None,
    locked_thread_ids: frozenset[str] | None = None,
) -> str:
    reply_counts = visible_reply_counts or {}
    pinned_ids = pinned_thread_ids or frozenset()
    locked_ids = locked_thread_ids or frozenset()
    lines = [
        "Command: list_index",
        f"Board-Tag: {board_tag or 'all'}",
        f"Entry-Count: {len(threads)}",
        "",
    ]
    for thread in threads:
        lines.append(
            "\t".join(
                [
                    thread.root.post_id,
                    thread.root.subject or "",
                    " ".join(thread.root.board_tags),
                    str(reply_counts.get(thread.root.post_id, len(thread.replies))),
                    "pinned" if thread.root.post_id in pinned_ids else "",
                    "locked" if thread.root.post_id in locked_ids else "",
                ]
            )
        )
    return "\n".join(lines) + "\n"


def render_thread_text(
    thread: Thread,
    *,
    hidden_post_ids: frozenset[str] | None = None,
    locked: bool = False,
) -> str:
    hidden_ids = hidden_post_ids or frozenset()
    lines = [
        f"Thread-ID: {thread.root.post_id}",
        f"Thread-State: {'locked' if locked else 'open'}",
        f"Record-Count: {1 + len(thread.replies)}",
        "",
        render_post_block(thread.root, hidden=thread.root.post_id in hidden_ids),
    ]
    for reply in thread.replies:
        lines.extend(["", render_post_block(reply, hidden=reply.post_id in hidden_ids)])
    return "\n".join(lines) + "\n"


def render_post_text(post: Post, *, hidden: bool = False) -> str:
    return render_post_block(post, hidden=hidden) + "\n"


def render_profile_text(summary: ProfileSummary) -> str:
    return render_profile_summary_text(summary)


def render_post_block(post: Post, *, hidden: bool = False) -> str:
    headers = [
        f"Post-ID: {post.post_id}",
        f"Board-Tags: {' '.join(post.board_tags)}",
    ]
    if post.subject:
        headers.append(f"Subject: {post.subject}")
    if post.thread_id:
        headers.append(f"Thread-ID: {post.thread_id}")
    if post.parent_id:
        headers.append(f"Parent-ID: {post.parent_id}")
    if root_thread_type(post):
        headers.append(f"Thread-Type: {root_thread_type(post)}")
    if is_task_root(post):
        assert post.task_metadata is not None
        headers.extend(
            [
                f"Task-Status: {post.task_metadata.status}",
                f"Task-Presentability-Impact: {post.task_metadata.presentability_impact:.2f}",
                f"Task-Implementation-Difficulty: {post.task_metadata.implementation_difficulty:.2f}",
            ]
        )
        if post.task_metadata.dependencies:
            headers.append(f"Task-Depends-On: {' '.join(post.task_metadata.dependencies)}")
        if post.task_metadata.sources:
            headers.append(f"Task-Sources: {'; '.join(post.task_metadata.sources)}")
    if hidden:
        headers.append("Moderation-State: hidden")
        return "\n".join(headers + ["", "[hidden by moderation]"])
    return "\n".join(headers + ["", post.body])


def render_moderation_log_text(
    records: tuple[ModerationRecord, ...],
    *,
    limit: int,
    before: str | None,
) -> str:
    lines = [
        "Command: get_moderation_log",
        f"Limit: {limit}",
        f"Before: {before or ''}",
        f"Entry-Count: {len(records)}",
        "",
    ]
    for record in records:
        lines.append(
            "\t".join(
                [
                    record.record_id,
                    record.timestamp,
                    record.action,
                    record.target_type,
                    record.target_id,
                    record.signer_fingerprint or "",
                ]
            )
        )
    return "\n".join(lines) + "\n"


def render_not_found_text(resource_name: str, resource_id: str) -> str:
    return (
        f"Error-Code: not_found\n"
        f"Resource: {resource_name}\n"
        f"Identifier: {resource_id}\n"
    )


def render_bad_request_text(message: str) -> str:
    return f"Error-Code: bad_request\nMessage: {message}\n"
