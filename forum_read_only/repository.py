from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Post:
    post_id: str
    board_tags: tuple[str, ...]
    subject: str
    thread_id: str | None
    parent_id: str | None
    body: str
    path: Path

    @property
    def is_root(self) -> bool:
        return self.thread_id is None and self.parent_id is None

    @property
    def root_thread_id(self) -> str:
        return self.thread_id or self.post_id


@dataclass(frozen=True)
class Thread:
    root: Post
    replies: tuple[Post, ...]


def parse_post(path: Path) -> Post:
    raw_text = path.read_text(encoding="ascii")
    header_text, separator, body_text = raw_text.partition("\n\n")
    if not separator:
        raise ValueError(f"post file is missing header/body separator: {path}")

    headers: dict[str, str] = {}
    for line in header_text.splitlines():
        if ": " not in line:
            raise ValueError(f"invalid header line in {path}: {line!r}")
        key, value = line.split(": ", 1)
        headers[key] = value.strip()

    post_id = headers.get("Post-ID")
    board_tags = headers.get("Board-Tags")
    if not post_id or not board_tags:
        raise ValueError(f"post file is missing required headers: {path}")

    subject = headers.get("Subject", "")
    thread_id = headers.get("Thread-ID")
    parent_id = headers.get("Parent-ID")

    return Post(
        post_id=post_id,
        board_tags=tuple(tag for tag in board_tags.split() if tag),
        subject=subject,
        thread_id=thread_id,
        parent_id=parent_id,
        body=body_text.rstrip("\n"),
        path=path,
    )


def load_posts(records_dir: Path) -> list[Post]:
    posts = [parse_post(path) for path in sorted(records_dir.glob("*.txt"))]
    return sorted(posts, key=lambda post: post.post_id)


def group_threads(posts: list[Post]) -> list[Thread]:
    roots = {post.post_id: post for post in posts if post.is_root}
    replies_by_thread: dict[str, list[Post]] = {post_id: [] for post_id in roots}

    for post in posts:
        if post.is_root:
            continue
        if post.root_thread_id in replies_by_thread:
            replies_by_thread[post.root_thread_id].append(post)

    threads = []
    for post_id in sorted(roots):
        replies = tuple(sorted(replies_by_thread[post_id], key=lambda post: post.post_id))
        threads.append(Thread(root=roots[post_id], replies=replies))
    return threads


def list_board_tags(posts: list[Post]) -> list[str]:
    tags = {tag for post in posts for tag in post.board_tags}
    return sorted(tags)


def list_threads_by_board(threads: list[Thread]) -> list[tuple[str, tuple[Thread, ...]]]:
    threads_by_board: dict[str, list[Thread]] = {}
    for thread in threads:
        for tag in thread.root.board_tags:
            threads_by_board.setdefault(tag, []).append(thread)

    ordered_sections = []
    for tag in sorted(threads_by_board):
        section_threads = tuple(sorted(threads_by_board[tag], key=lambda thread: thread.root.post_id))
        ordered_sections.append((tag, section_threads))
    return ordered_sections
