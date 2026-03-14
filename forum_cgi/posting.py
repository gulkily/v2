from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from forum_read_only.repository import Post, index_posts, load_posts, parse_post_text


class PostingError(Exception):
    def __init__(self, error_code: str, message: str, *, status: str = "400 Bad Request") -> None:
        super().__init__(message)
        self.error_code = error_code
        self.message = message
        self.status = status


@dataclass(frozen=True)
class CommandPreview:
    command_name: str
    record_id: str
    thread_id: str
    stored_path: str
    commit_message: str
    parent_id: str | None = None


def get_repo_root() -> Path:
    env_root = os.environ.get("FORUM_REPO_ROOT")
    if env_root:
        return Path(env_root).resolve()
    return Path(__file__).resolve().parent.parent


def records_dir(repo_root: Path) -> Path:
    return repo_root / "records" / "posts"


def read_ascii_payload() -> str:
    raw_bytes = sys.stdin.buffer.read()
    if not raw_bytes:
        raise PostingError("bad_request", "missing request body")
    try:
        payload = raw_bytes.decode("ascii")
    except UnicodeDecodeError as exc:
        raise PostingError("bad_request", "request body must be ASCII") from exc
    if not payload.strip():
        raise PostingError("bad_request", "request body must not be blank")
    return payload


def parse_payload(payload_text: str) -> Post:
    try:
        return parse_post_text(payload_text)
    except ValueError as exc:
        raise PostingError("bad_request", str(exc)) from exc


def resolve_storage_path(repo_root: Path, post_id: str) -> Path:
    return records_dir(repo_root) / f"{post_id}.txt"


def build_commit_message(command_name: str, record_id: str) -> str:
    return f"{command_name}: {record_id}"


def validate_create_thread(post: Post) -> None:
    if post.thread_id is not None:
        raise PostingError("bad_request", "Thread-ID must be omitted for create_thread")
    if post.parent_id is not None:
        raise PostingError("bad_request", "Parent-ID must be omitted for create_thread")


def validate_create_reply(post: Post, repo_root: Path) -> None:
    if not post.thread_id:
        raise PostingError("bad_request", "Thread-ID is required for create_reply")
    if not post.parent_id:
        raise PostingError("bad_request", "Parent-ID is required for create_reply")

    posts = load_posts(records_dir(repo_root))
    posts_by_id = index_posts(posts)
    thread_root = posts_by_id.get(post.thread_id)
    if thread_root is None or not thread_root.is_root:
        raise PostingError("not_found", f"unknown thread: {post.thread_id}", status="404 Not Found")

    parent_post = posts_by_id.get(post.parent_id)
    if parent_post is None:
        raise PostingError("not_found", f"unknown parent: {post.parent_id}", status="404 Not Found")
    if parent_post.root_thread_id != post.thread_id:
        raise PostingError("bad_request", "Parent-ID must point to a post in the same thread")


def ensure_post_id_available(post: Post, repo_root: Path) -> None:
    if resolve_storage_path(repo_root, post.post_id).exists():
        raise PostingError("conflict", f"post already exists: {post.post_id}", status="409 Conflict")


def build_preview(command_name: str, post: Post, repo_root: Path) -> CommandPreview:
    return CommandPreview(
        command_name=command_name,
        record_id=post.post_id,
        thread_id=post.root_thread_id,
        parent_id=post.parent_id,
        stored_path=str(resolve_storage_path(repo_root, post.post_id).relative_to(repo_root)),
        commit_message=build_commit_message(command_name, post.post_id),
    )


def write_post_file(post: Post, repo_root: Path, payload_text: str) -> Path:
    post_path = resolve_storage_path(repo_root, post.post_id)
    post_path.write_text(payload_text, encoding="ascii")
    return post_path


def commit_post(repo_root: Path, post_path: Path, *, message: str) -> str:
    env = os.environ.copy()
    env.setdefault("GIT_AUTHOR_NAME", "Forum CGI")
    env.setdefault("GIT_AUTHOR_EMAIL", "forum-cgi@example.invalid")
    env.setdefault("GIT_COMMITTER_NAME", env["GIT_AUTHOR_NAME"])
    env.setdefault("GIT_COMMITTER_EMAIL", env["GIT_AUTHOR_EMAIL"])

    relative_path = str(post_path.relative_to(repo_root))
    subprocess.run(
        ["git", "-C", str(repo_root), "add", relative_path],
        check=True,
        env=env,
    )
    subprocess.run(
        [
            "git",
            "-C",
            str(repo_root),
            "commit",
            "--no-gpg-sign",
            "--only",
            "-m",
            message,
            "--",
            relative_path,
        ],
        check=True,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
        check=True,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    ).stdout.strip()
