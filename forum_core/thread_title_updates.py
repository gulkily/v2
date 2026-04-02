from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from forum_core.identity import build_identity_id, fingerprint_from_public_key_path
from forum_core.moderation import is_authorized_moderator
from forum_core.public_keys import resolve_public_key_from_signature
from forum_core.runtime_env import env_flag_enabled


THREAD_TITLE_ANY_USER_EDIT_ENV = "FORUM_ENABLE_THREAD_TITLE_ANY_USER_EDIT"
MAX_THREAD_TITLE_LENGTH = 72


@dataclass(frozen=True)
class ThreadTitleUpdateRecord:
    record_id: str
    thread_id: str
    timestamp: str
    title: str
    path: Path
    signature_path: Path | None = None
    public_key_path: Path | None = None
    signer_fingerprint: str | None = None
    identity_id: str | None = None


def thread_title_update_sort_key(record: ThreadTitleUpdateRecord) -> tuple[str, str]:
    return record.timestamp, record.record_id


def thread_title_updates_dir(repo_root: Path) -> Path:
    return repo_root / "records" / "thread-title-updates"


def thread_title_any_user_edit_enabled(env: dict[str, str] | None = None) -> bool:
    return env_flag_enabled(THREAD_TITLE_ANY_USER_EDIT_ENV, env=env)


def ensure_timestamp_text(timestamp_text: str) -> str:
    try:
        datetime.strptime(timestamp_text, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as exc:
        raise ValueError("Timestamp must use UTC ISO-8601 form YYYY-MM-DDTHH:MM:SSZ") from exc
    return timestamp_text


def normalize_thread_title(title: str) -> str:
    value = title.strip()
    if not value:
        raise ValueError("thread title must not be blank")
    if "\n" in value or "\r" in value:
        raise ValueError("thread title must be a single line")
    try:
        value.encode("ascii")
    except UnicodeEncodeError as exc:
        raise ValueError("thread title must be ASCII") from exc
    if len(value) > MAX_THREAD_TITLE_LENGTH:
        raise ValueError(f"thread title must be at most {MAX_THREAD_TITLE_LENGTH} characters")
    return value


def parse_thread_title_update_text(
    raw_text: str,
    *,
    source_path: Path | None = None,
) -> ThreadTitleUpdateRecord:
    header_text, separator, body_text = raw_text.partition("\n\n")
    if not separator:
        raise ValueError("thread-title-update text is missing header/body separator")

    headers: dict[str, str] = {}
    for line in header_text.splitlines():
        if ": " not in line:
            raise ValueError(f"invalid thread-title-update header line: {line!r}")
        key, value = line.split(": ", 1)
        headers[key] = value.strip()

    record_id = headers.get("Record-ID")
    thread_id = headers.get("Thread-ID")
    timestamp = headers.get("Timestamp")
    if not record_id or not thread_id or not timestamp:
        raise ValueError("thread-title-update text is missing required headers")

    return ThreadTitleUpdateRecord(
        record_id=record_id,
        thread_id=thread_id,
        timestamp=ensure_timestamp_text(timestamp),
        title=normalize_thread_title(body_text.rstrip("\n")),
        path=source_path or Path("<request>"),
    )


def resolve_thread_title_update_signature_path(record_path: Path) -> Path | None:
    candidate = record_path.with_name(f"{record_path.name}.asc")
    return candidate if candidate.exists() else None


def resolve_thread_title_update_public_key_path(record_path: Path) -> Path | None:
    candidate = record_path.with_name(f"{record_path.name}.pub.asc")
    if candidate.exists():
        return candidate
    return resolve_public_key_from_signature(
        repo_root=record_path.parents[2],
        signature_path=resolve_thread_title_update_signature_path(record_path),
    )


def parse_thread_title_update_record(path: Path) -> ThreadTitleUpdateRecord:
    record = parse_thread_title_update_text(path.read_text(encoding="ascii"), source_path=path)
    signature_path = resolve_thread_title_update_signature_path(path)
    public_key_path = resolve_thread_title_update_public_key_path(path)

    signer_fingerprint = None
    identity_id = None
    if public_key_path is not None:
        signer_fingerprint = fingerprint_from_public_key_path(public_key_path)
        identity_id = build_identity_id(signer_fingerprint)

    return ThreadTitleUpdateRecord(
        record_id=record.record_id,
        thread_id=record.thread_id,
        timestamp=record.timestamp,
        title=record.title,
        path=record.path,
        signature_path=signature_path,
        public_key_path=public_key_path,
        signer_fingerprint=signer_fingerprint,
        identity_id=identity_id,
    )


def load_thread_title_update_records(records_dir: Path) -> list[ThreadTitleUpdateRecord]:
    if not records_dir.exists():
        return []
    records = [parse_thread_title_update_record(path) for path in sorted(records_dir.glob("*.txt"))]
    return sorted(records, key=thread_title_update_sort_key)


def resolve_current_thread_title(
    *,
    thread_id: str,
    root_subject: str,
    updates: list[ThreadTitleUpdateRecord],
) -> str:
    candidates = [record for record in updates if record.thread_id == thread_id]
    if not candidates:
        return root_subject
    return max(candidates, key=thread_title_update_sort_key).title


def signer_can_update_thread_title(
    *,
    thread_owner_identity_id: str | None,
    signer_identity_id: str | None,
    signer_fingerprint: str | None,
    env: dict[str, str] | None = None,
) -> bool:
    if signer_identity_id is not None and signer_identity_id == thread_owner_identity_id:
        return True
    if signer_fingerprint is not None and is_authorized_moderator(signer_fingerprint, env=env):
        return True
    if thread_title_any_user_edit_enabled(env):
        return signer_identity_id is not None or signer_fingerprint is not None
    return False
