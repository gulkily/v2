from __future__ import annotations

from forum_read_only.repository import Post, Thread


def render_api_home_text(*, post_count: int, thread_count: int, board_tags: list[str]) -> str:
    lines = [
        "FORUM-API/1",
        "Mode: read-only",
        "Available-Commands: list_index get_thread get_post",
        f"Post-Count: {post_count}",
        f"Thread-Count: {thread_count}",
        f"Board-Tags: {' '.join(board_tags)}",
        "",
        "Routes:",
        "/api/",
        "/api/list_index",
        "/api/get_thread?thread_id=<thread-id>",
        "/api/get_post?post_id=<post-id>",
    ]
    return "\n".join(lines) + "\n"


def render_index_text(threads: list[Thread], *, board_tag: str | None = None) -> str:
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
                    str(len(thread.replies)),
                ]
            )
        )
    return "\n".join(lines) + "\n"


def render_thread_text(thread: Thread) -> str:
    lines = [
        f"Thread-ID: {thread.root.post_id}",
        f"Record-Count: {1 + len(thread.replies)}",
        "",
        render_post_block(thread.root),
    ]
    for reply in thread.replies:
        lines.extend(["", render_post_block(reply)])
    return "\n".join(lines) + "\n"


def render_post_text(post: Post) -> str:
    return render_post_block(post) + "\n"


def render_post_block(post: Post) -> str:
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
    return "\n".join(headers + ["", post.body])


def render_not_found_text(resource_name: str, resource_id: str) -> str:
    return (
        f"Error-Code: not_found\n"
        f"Resource: {resource_name}\n"
        f"Identifier: {resource_id}\n"
    )


def render_bad_request_text(message: str) -> str:
    return f"Error-Code: bad_request\nMessage: {message}\n"
