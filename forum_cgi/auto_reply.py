from __future__ import annotations

import os
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from forum_cgi.posting import PostingError, ensure_ascii_text
from forum_cgi.signing import sign_detached_payload
from forum_core.identity import build_identity_id, fingerprint_from_public_key_text
from forum_core.llm_provider import get_llm_model, run_llm
from forum_read_only.repository import Post


class AutoReplyError(RuntimeError):
    pass


@dataclass(frozen=True)
class AssistantSigningConfig:
    private_key_path: Path
    public_key_path: Path


@dataclass(frozen=True)
class SignedPayload:
    payload_text: str
    signature_text: str
    public_key_text: str
    signer_fingerprint: str
    identity_id: str


def thread_auto_reply_enabled() -> bool:
    return _env_flag("FORUM_ENABLE_THREAD_AUTO_REPLY")


def get_thread_auto_reply_signing_config() -> AssistantSigningConfig:
    private_key_path = _required_path_env("FORUM_THREAD_AUTO_REPLY_PRIVATE_KEY_PATH")
    public_key_path = _required_path_env("FORUM_THREAD_AUTO_REPLY_PUBLIC_KEY_PATH")
    return AssistantSigningConfig(
        private_key_path=private_key_path,
        public_key_path=public_key_path,
    )


def generate_thread_auto_reply(*, thread_post: Post, repo_root: Path) -> SignedPayload:
    if not thread_post.is_root:
        raise AutoReplyError("thread auto reply requires a thread root post")

    signing_config = get_thread_auto_reply_signing_config()
    public_key_text = _read_ascii_file(signing_config.public_key_path, env_name="FORUM_THREAD_AUTO_REPLY_PUBLIC_KEY_PATH")
    private_key_text = _read_ascii_file(
        signing_config.private_key_path,
        env_name="FORUM_THREAD_AUTO_REPLY_PRIVATE_KEY_PATH",
    )
    signer_fingerprint = fingerprint_from_public_key_text(public_key_text)
    identity_id = build_identity_id(signer_fingerprint)

    output_text = run_llm(
        [
            {
                "role": "system",
                "content": (
                    "Write one brief helpful forum reply in plain ASCII only. "
                    "Use at most four short paragraphs. Do not mention being an AI model. "
                    "Do not use markdown headings or bullet lists unless necessary."
                ),
            },
            {
                "role": "user",
                "content": build_thread_auto_reply_prompt(thread_post),
            },
        ]
    )
    body = normalize_auto_reply_body(output_text)
    payload_text = build_auto_reply_payload(thread_post=thread_post, body_text=body)
    signature_text = sign_detached_payload(
        payload_text=payload_text,
        private_key_text=private_key_text,
    )
    return SignedPayload(
        payload_text=payload_text,
        signature_text=signature_text,
        public_key_text=public_key_text,
        signer_fingerprint=signer_fingerprint,
        identity_id=identity_id,
    )


def build_thread_auto_reply_prompt(thread_post: Post) -> str:
    subject = thread_post.subject.strip() or "(no subject)"
    body = thread_post.body.strip() or "(no body)"
    board_tags = " ".join(thread_post.board_tags) or "(none)"
    return (
        "A forum user created a new thread.\n"
        f"Board tags: {board_tags}\n"
        f"Subject: {subject}\n"
        "Thread body follows.\n\n"
        f"{body}\n\n"
        "Write one short, helpful reply that directly responds to the thread."
    )


def normalize_auto_reply_body(output_text: str) -> str:
    normalized = output_text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not normalized:
        raise AutoReplyError("Dedalus returned an empty auto reply")
    try:
        normalized.encode("ascii")
    except UnicodeEncodeError as exc:
        raise AutoReplyError("Dedalus returned non-ASCII auto reply text") from exc
    return ensure_ascii_text(normalized + "\n", field_name="auto_reply_body")


def build_auto_reply_payload(*, thread_post: Post, body_text: str) -> str:
    ensure_ascii_text(body_text, field_name="auto_reply_body")
    headers = [
        f"Post-ID: {generate_auto_reply_post_id(body_text)}",
        f"Board-Tags: {' '.join(thread_post.board_tags)}",
        f"Thread-ID: {thread_post.post_id}",
        f"Parent-ID: {thread_post.post_id}",
    ]
    return f"{chr(10).join(headers)}\n\n{body_text}"


def generate_auto_reply_post_id(body_text: str) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    slug = slug_from_text(body_text)
    return f"reply-{timestamp}-{slug}-{secrets.token_hex(4)}"


def slug_from_text(text: str) -> str:
    first_line = ""
    for line in text.splitlines():
        trimmed = line.strip().lower()
        if trimmed:
            first_line = trimmed
            break
    slug_chars: list[str] = []
    previous_dash = False
    for character in first_line:
        if character.isalnum() and character.isascii():
            slug_chars.append(character)
            previous_dash = False
            continue
        if not previous_dash:
            slug_chars.append("-")
            previous_dash = True
    slug = "".join(slug_chars).strip("-")
    return slug[:24] or "reply"


def _env_flag(name: str) -> bool:
    value = os.getenv(name, "").strip().lower()
    return value in {"1", "true", "yes", "on"}


def _required_path_env(name: str) -> Path:
    raw_value = os.getenv(name, "").strip()
    if not raw_value:
        raise AutoReplyError(f"{name} is not configured.")
    return Path(raw_value).expanduser().resolve()


def _read_ascii_file(path: Path, *, env_name: str) -> str:
    try:
        raw_text = path.read_text(encoding="ascii")
    except FileNotFoundError as exc:
        raise AutoReplyError(f"{env_name} file does not exist: {path}") from exc
    except UnicodeDecodeError as exc:
        raise AutoReplyError(f"{env_name} must point to an ASCII-armored key file") from exc
    try:
        return ensure_ascii_text(raw_text, field_name=env_name)
    except PostingError as exc:
        raise AutoReplyError(exc.message) from exc


def get_thread_auto_reply_model() -> str:
    return get_llm_model()
