from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from forum_core.identity import build_identity_id, fingerprint_from_public_key_path, normalize_fingerprint
from forum_core.public_keys import resolve_public_key_from_signature


ALLOWED_MODERATION_ACTIONS = ("hide", "lock", "pin", "unpin")
ALLOWED_TARGET_TYPES = ("post", "thread")
THREAD_ONLY_ACTIONS = frozenset({"lock", "pin", "unpin"})
MODERATOR_ALLOWLIST_ENV = "FORUM_MODERATOR_FINGERPRINTS"


@dataclass(frozen=True)
class ModerationRecord:
    record_id: str
    action: str
    target_type: str
    target_id: str
    timestamp: str
    reason: str
    path: Path
    signature_path: Path | None = None
    public_key_path: Path | None = None
    signer_fingerprint: str | None = None
    identity_id: str | None = None


@dataclass(frozen=True)
class ModerationState:
    hidden_post_ids: frozenset[str]
    hidden_thread_ids: frozenset[str]
    locked_thread_ids: frozenset[str]
    pinned_thread_ids: frozenset[str]

    def hides_thread(self, thread_id: str) -> bool:
        return thread_id in self.hidden_thread_ids

    def hides_post(self, post_id: str) -> bool:
        return post_id in self.hidden_post_ids

    def locks_thread(self, thread_id: str) -> bool:
        return thread_id in self.locked_thread_ids

    def pins_thread(self, thread_id: str) -> bool:
        return thread_id in self.pinned_thread_ids


def moderation_sort_key(record: ModerationRecord) -> tuple[str, str]:
    return record.timestamp, record.record_id


def moderation_records_dir(repo_root: Path) -> Path:
    return repo_root / "records" / "moderation"


def ensure_timestamp_text(timestamp_text: str) -> str:
    try:
        datetime.strptime(timestamp_text, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as exc:
        raise ValueError("Timestamp must use UTC ISO-8601 form YYYY-MM-DDTHH:MM:SSZ") from exc
    return timestamp_text


def parse_moderation_text(raw_text: str, *, source_path: Path | None = None) -> ModerationRecord:
    header_text, separator, body_text = raw_text.partition("\n\n")
    if not separator:
        raise ValueError("moderation text is missing header/body separator")

    headers: dict[str, str] = {}
    for line in header_text.splitlines():
        if ": " not in line:
            raise ValueError(f"invalid moderation header line: {line!r}")
        key, value = line.split(": ", 1)
        headers[key] = value.strip()

    record_id = headers.get("Record-ID")
    action = (headers.get("Action") or "").strip().lower()
    target_type = (headers.get("Target-Type") or "").strip().lower()
    target_id = headers.get("Target-ID")
    timestamp = headers.get("Timestamp")

    if not record_id or not action or not target_type or not target_id or not timestamp:
        raise ValueError("moderation text is missing required headers")
    if action not in ALLOWED_MODERATION_ACTIONS:
        raise ValueError(f"unsupported moderation action: {action}")
    if target_type not in ALLOWED_TARGET_TYPES:
        raise ValueError(f"unsupported moderation target type: {target_type}")
    if action in THREAD_ONLY_ACTIONS and target_type != "thread":
        raise ValueError(f"{action} moderation actions must target a thread")

    return ModerationRecord(
        record_id=record_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        timestamp=ensure_timestamp_text(timestamp),
        reason=body_text.rstrip("\n"),
        path=source_path or Path("<request>"),
    )


def resolve_moderation_signature_path(record_path: Path) -> Path | None:
    candidate = record_path.with_name(f"{record_path.name}.asc")
    return candidate if candidate.exists() else None


def resolve_moderation_public_key_path(record_path: Path) -> Path | None:
    candidate = record_path.with_name(f"{record_path.name}.pub.asc")
    if candidate.exists():
        return candidate
    return resolve_public_key_from_signature(
        repo_root=record_path.parents[2],
        signature_path=resolve_moderation_signature_path(record_path),
    )


def parse_moderation_record(path: Path) -> ModerationRecord:
    record = parse_moderation_text(path.read_text(encoding="ascii"), source_path=path)
    signature_path = resolve_moderation_signature_path(path)
    public_key_path = resolve_moderation_public_key_path(path)

    signer_fingerprint = None
    identity_id = None
    if public_key_path is not None:
        signer_fingerprint = fingerprint_from_public_key_path(public_key_path)
        identity_id = build_identity_id(signer_fingerprint)

    return ModerationRecord(
        record_id=record.record_id,
        action=record.action,
        target_type=record.target_type,
        target_id=record.target_id,
        timestamp=record.timestamp,
        reason=record.reason,
        path=record.path,
        signature_path=signature_path,
        public_key_path=public_key_path,
        signer_fingerprint=signer_fingerprint,
        identity_id=identity_id,
    )


def load_moderation_records(records_dir: Path) -> list[ModerationRecord]:
    if not records_dir.exists():
        return []
    records = [parse_moderation_record(path) for path in sorted(records_dir.glob("*.txt"))]
    return sorted(records, key=moderation_sort_key)
def derive_moderation_state(records: list[ModerationRecord]) -> ModerationState:
    hidden_post_ids: set[str] = set()
    hidden_thread_ids: set[str] = set()
    locked_thread_ids: set[str] = set()
    pin_actions: dict[str, str] = {}

    for record in sorted(records, key=moderation_sort_key):
        if record.action == "hide":
            if record.target_type == "thread":
                hidden_thread_ids.add(record.target_id)
            else:
                hidden_post_ids.add(record.target_id)
            continue

        if record.action == "lock":
            locked_thread_ids.add(record.target_id)
            continue

        if record.action in {"pin", "unpin"}:
            pin_actions[record.target_id] = record.action

    pinned_thread_ids = {
        target_id
        for target_id, action in pin_actions.items()
        if action == "pin"
    }
    return ModerationState(
        hidden_post_ids=frozenset(hidden_post_ids),
        hidden_thread_ids=frozenset(hidden_thread_ids),
        locked_thread_ids=frozenset(locked_thread_ids),
        pinned_thread_ids=frozenset(pinned_thread_ids),
    )


def thread_is_hidden(state: ModerationState, thread_id: str) -> bool:
    return state.hides_thread(thread_id) or state.hides_post(thread_id)


def post_is_hidden(state: ModerationState, post_id: str, root_thread_id: str) -> bool:
    return state.hides_post(post_id) or thread_is_hidden(state, root_thread_id)


def moderation_log_slice(
    records: list[ModerationRecord],
    *,
    limit: int,
    before: str | None = None,
) -> tuple[ModerationRecord, ...]:
    ordered = sorted(records, key=moderation_sort_key, reverse=True)
    if before:
        for index, record in enumerate(ordered):
            if record.record_id == before:
                ordered = ordered[index + 1 :]
                break
        else:
            raise ValueError(f"unknown moderation cursor: {before}")
    return tuple(ordered[:limit])


def moderator_fingerprint_allowlist(env: dict[str, str] | None = None) -> frozenset[str]:
    source_env = env or os.environ
    raw_value = source_env.get(MODERATOR_ALLOWLIST_ENV, "")
    tokens = [
        token
        for token in raw_value.replace(",", " ").split()
        if token.strip()
    ]
    return frozenset(normalize_fingerprint(token) for token in tokens)


def is_authorized_moderator(fingerprint: str, env: dict[str, str] | None = None) -> bool:
    normalized = normalize_fingerprint(fingerprint)
    return normalized in moderator_fingerprint_allowlist(env)
