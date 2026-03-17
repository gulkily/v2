from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from forum_core.identity import build_bootstrap_record_id
from forum_core.moderation import derive_moderation_state, load_moderation_records, moderation_records_dir, post_is_hidden, thread_is_hidden
from forum_core.post_index import refresh_post_index_after_commit
from forum_web.repository import Post, index_posts, load_posts, parse_post_text


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


@dataclass(frozen=True)
class StoredArtifacts:
    post_path: str
    signature_path: str | None = None
    public_key_path: str | None = None
    identity_bootstrap_path: str | None = None


def get_repo_root() -> Path:
    env_root = os.environ.get("FORUM_REPO_ROOT")
    if env_root:
        return Path(env_root).resolve()
    return Path(__file__).resolve().parent.parent


def records_dir(repo_root: Path) -> Path:
    return repo_root / "records" / "posts"


def identity_records_dir(repo_root: Path) -> Path:
    return repo_root / "records" / "identity"


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

    moderation_state = derive_moderation_state(load_moderation_records(moderation_records_dir(repo_root)))
    if thread_is_hidden(moderation_state, post.thread_id):
        raise PostingError("not_found", f"unknown thread: {post.thread_id}", status="404 Not Found")
    if moderation_state.locks_thread(post.thread_id):
        raise PostingError("conflict", f"thread is locked by moderation: {post.thread_id}", status="409 Conflict")
    if post_is_hidden(moderation_state, post.parent_id, post.thread_id):
        raise PostingError("conflict", f"parent is hidden by moderation: {post.parent_id}", status="409 Conflict")


def ensure_post_id_available(post: Post, repo_root: Path) -> None:
    if resolve_storage_path(repo_root, post.post_id).exists():
        raise PostingError("conflict", f"post already exists: {post.post_id}", status="409 Conflict")


def ensure_ascii_text(value: str, *, field_name: str) -> str:
    try:
        value.encode("ascii")
    except UnicodeEncodeError as exc:
        raise PostingError("bad_request", f"{field_name} must be ASCII") from exc
    if not value.strip():
        raise PostingError("bad_request", f"{field_name} must not be blank")
    return value


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


def resolve_signature_path(repo_root: Path, post_id: str) -> Path:
    return records_dir(repo_root) / f"{post_id}.txt.asc"


def resolve_public_key_path(repo_root: Path, post_id: str) -> Path:
    return records_dir(repo_root) / f"{post_id}.txt.pub.asc"


def resolve_identity_bootstrap_path(repo_root: Path, identity_id: str) -> Path:
    return identity_records_dir(repo_root) / f"{build_bootstrap_record_id(identity_id)}.txt"


def write_ascii_file(path: Path, text: str) -> Path:
    path.write_text(text, encoding="ascii")
    return path


def store_post(
    command_name: str,
    post: Post,
    repo_root: Path,
    payload_text: str,
    *,
    signature_text: str | None = None,
    public_key_text: str | None = None,
    identity_bootstrap_path: Path | None = None,
    identity_bootstrap_text: str | None = None,
) -> tuple[str, StoredArtifacts]:
    ensure_post_id_available(post, repo_root)
    post_path = write_post_file(post, repo_root, payload_text)
    signature_path = None
    public_key_path = None
    stored_identity_bootstrap_path = None
    paths = [post_path]
    if signature_text is not None:
        signature_path = write_ascii_file(
            resolve_signature_path(repo_root, post.post_id),
            ensure_ascii_text(signature_text, field_name="signature"),
        )
        paths.append(signature_path)
    if public_key_text is not None:
        public_key_path = write_ascii_file(
            resolve_public_key_path(repo_root, post.post_id),
            ensure_ascii_text(public_key_text, field_name="public_key"),
        )
        paths.append(public_key_path)
    if identity_bootstrap_path is not None and identity_bootstrap_text is not None:
        identity_bootstrap_path.parent.mkdir(parents=True, exist_ok=True)
        stored_identity_bootstrap_path = write_ascii_file(
            identity_bootstrap_path,
            ensure_ascii_text(identity_bootstrap_text, field_name="identity_bootstrap"),
        )
        paths.append(stored_identity_bootstrap_path)

    commit_id = commit_post(
        repo_root,
        paths,
        message=build_commit_message(command_name, post.post_id),
    )
    return commit_id, StoredArtifacts(
        post_path=str(post_path.relative_to(repo_root)),
        signature_path=str(signature_path.relative_to(repo_root)) if signature_path else None,
        public_key_path=str(public_key_path.relative_to(repo_root)) if public_key_path else None,
        identity_bootstrap_path=(
            str(stored_identity_bootstrap_path.relative_to(repo_root))
            if stored_identity_bootstrap_path
            else None
        ),
    )


def commit_post(repo_root: Path, paths: list[Path], *, message: str) -> str:
    env = os.environ.copy()
    env.setdefault("GIT_AUTHOR_NAME", "Forum CGI")
    env.setdefault("GIT_AUTHOR_EMAIL", "forum-cgi@example.invalid")
    env.setdefault("GIT_COMMITTER_NAME", env["GIT_AUTHOR_NAME"])
    env.setdefault("GIT_COMMITTER_EMAIL", env["GIT_AUTHOR_EMAIL"])

    relative_paths = [str(path.relative_to(repo_root)) for path in paths]
    subprocess.run(
        ["git", "-C", str(repo_root), "add", *relative_paths],
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
            *relative_paths,
        ],
        check=True,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    commit_id = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
        check=True,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    ).stdout.strip()
    refresh_post_index_after_commit(
        repo_root,
        commit_id=commit_id,
        touched_paths=tuple(relative_paths),
    )
    return commit_id
