from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from forum_core.identity import build_identity_id, fingerprint_from_public_key_path
from forum_core.public_keys import resolve_public_key_from_signature


@dataclass(frozen=True)
class TaskRootMetadata:
    status: str
    presentability_impact: float
    implementation_difficulty: float
    dependencies: tuple[str, ...]
    sources: tuple[str, ...] = ()


@dataclass(frozen=True)
class Post:
    post_id: str
    board_tags: tuple[str, ...]
    subject: str
    thread_id: str | None
    parent_id: str | None
    body: str
    path: Path
    thread_type: str | None = None
    task_metadata: TaskRootMetadata | None = None
    signature_path: Path | None = None
    public_key_path: Path | None = None
    signer_fingerprint: str | None = None
    identity_id: str | None = None
    proof_of_work: str | None = None

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


def parse_rating_value(raw_value: str, *, header_name: str) -> float:
    try:
        value = float(raw_value)
    except ValueError as exc:
        raise ValueError(f"{header_name} must be a decimal rating") from exc
    if value < 0 or value > 1:
        raise ValueError(f"{header_name} must be between 0 and 1")
    return value


def parse_task_dependencies(raw_value: str) -> tuple[str, ...]:
    return tuple(part for part in raw_value.split() if part)


def split_semicolon_header(raw_value: str) -> tuple[str, ...]:
    return tuple(part.strip() for part in raw_value.split(";") if part.strip())


def require_header(headers: dict[str, str], header_name: str) -> str:
    value = headers.get(header_name, "").strip()
    if not value:
        raise ValueError(f"post text is missing required header: {header_name}")
    return value


def normalize_thread_type(raw_value: str | None) -> str | None:
    if raw_value is None:
        return None
    value = raw_value.strip()
    if not value:
        return None
    if not value.replace("-", "").isalnum() or not value[0].isalpha() or value.lower() != value:
        raise ValueError("Thread-Type must be lowercase letters, digits, or hyphens")
    return value


def has_task_headers(headers: dict[str, str]) -> bool:
    return any(key.startswith("Task-") for key in headers)


def parse_task_root_metadata(headers: dict[str, str]) -> TaskRootMetadata:
    return TaskRootMetadata(
        status=require_header(headers, "Task-Status"),
        presentability_impact=parse_rating_value(
            require_header(headers, "Task-Presentability-Impact"),
            header_name="Task-Presentability-Impact",
        ),
        implementation_difficulty=parse_rating_value(
            require_header(headers, "Task-Implementation-Difficulty"),
            header_name="Task-Implementation-Difficulty",
        ),
        dependencies=parse_task_dependencies(headers.get("Task-Depends-On", "")),
        sources=split_semicolon_header(headers.get("Task-Sources", "")),
    )


def root_thread_type(post: Post) -> str | None:
    return post.thread_type if post.is_root else None


def is_task_root(post: Post) -> bool:
    return root_thread_type(post) == "task" and post.task_metadata is not None


def parse_post_text(raw_text: str, *, source_path: Path | None = None) -> Post:
    header_text, separator, body_text = raw_text.partition("\n\n")
    if not separator:
        raise ValueError("post text is missing header/body separator")

    headers: dict[str, str] = {}
    for line in header_text.splitlines():
        if ": " not in line:
            raise ValueError(f"invalid header line: {line!r}")
        key, value = line.split(": ", 1)
        headers[key] = value.strip()

    post_id = headers.get("Post-ID")
    board_tags = headers.get("Board-Tags")
    if not post_id or not board_tags:
        raise ValueError("post text is missing required headers")

    subject = headers.get("Subject", "")
    thread_id = headers.get("Thread-ID")
    parent_id = headers.get("Parent-ID")
    proof_of_work = headers.get("Proof-Of-Work")
    thread_type = normalize_thread_type(headers.get("Thread-Type"))
    task_metadata = None

    if thread_id or parent_id:
        if thread_type is not None:
            raise ValueError("Thread-Type is only valid on thread roots")
        if has_task_headers(headers):
            raise ValueError("Task-* headers are only valid on task root threads")
    elif thread_type == "task":
        task_metadata = parse_task_root_metadata(headers)
        if not body_text.strip():
            raise ValueError("task root body must not be blank")
    elif has_task_headers(headers):
        raise ValueError("Task-* headers require Thread-Type: task")

    return Post(
        post_id=post_id,
        board_tags=tuple(tag for tag in board_tags.split() if tag),
        subject=subject,
        thread_id=thread_id,
        parent_id=parent_id,
        body=body_text.rstrip("\n"),
        path=source_path or Path("<request>"),
        thread_type=thread_type,
        task_metadata=task_metadata,
        proof_of_work=proof_of_work,
    )


def parse_post(path: Path) -> Post:
    post = parse_post_text(path.read_text(encoding="ascii"), source_path=path)
    signature_path = resolve_signature_path(path)
    public_key_path = resolve_public_key_path(path)

    signer_fingerprint = None
    identity_id = None
    if public_key_path is not None:
        signer_fingerprint = fingerprint_from_public_key_path(public_key_path)
        identity_id = build_identity_id(signer_fingerprint)

    return Post(
        post_id=post.post_id,
        board_tags=post.board_tags,
        subject=post.subject,
        thread_id=post.thread_id,
        parent_id=post.parent_id,
        body=post.body,
        path=post.path,
        thread_type=post.thread_type,
        task_metadata=post.task_metadata,
        signature_path=signature_path,
        public_key_path=public_key_path,
        signer_fingerprint=signer_fingerprint,
        identity_id=identity_id,
        proof_of_work=post.proof_of_work,
    )


def resolve_signature_path(post_path: Path) -> Path | None:
    candidate = post_path.with_name(f"{post_path.name}.asc")
    return candidate if candidate.exists() else None


def resolve_public_key_path(post_path: Path) -> Path | None:
    candidate = post_path.with_name(f"{post_path.name}.pub.asc")
    if candidate.exists():
        return candidate
    return resolve_public_key_from_signature(repo_root=post_path.parents[2], signature_path=resolve_signature_path(post_path))


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


def index_posts(posts: list[Post]) -> dict[str, Post]:
    return {post.post_id: post for post in posts}


def index_threads(threads: list[Thread]) -> dict[str, Thread]:
    return {thread.root.post_id: thread for thread in threads}
