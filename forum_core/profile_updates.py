from __future__ import annotations

import os
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from forum_core.identity import build_identity_id, fingerprint_from_public_key_path
from forum_core.identity_links import ensure_identity_id_text
from forum_core.public_keys import resolve_public_key_from_signature
from forum_core.runtime_env import env_flag_enabled


ALLOWED_PROFILE_UPDATE_ACTIONS = ("set_display_name",)
MIN_DISPLAY_NAME_LENGTH = 3
MAX_DISPLAY_NAME_LENGTH = 32
PREVENT_DUPLICATE_USERNAMES_ENV = "FORUM_PREVENT_DUPLICATE_USERNAMES"
DISPLAY_NAME_PATTERN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
RESERVED_DISPLAY_NAMES = frozenset(
    {
        "activity",
        "admin",
        "api",
        "assets",
        "compose",
        "instance",
        "profiles",
        "threads",
        "user",
    }
)


@dataclass(frozen=True)
class ProfileUpdateRecord:
    record_id: str
    action: str
    source_identity_id: str
    timestamp: str
    display_name: str
    path: Path
    signature_path: Path | None = None
    public_key_path: Path | None = None
    signer_fingerprint: str | None = None
    identity_id: str | None = None


@dataclass(frozen=True)
class ResolvedDisplayName:
    display_name: str
    record_id: str
    source_identity_id: str
    timestamp: str


def profile_update_sort_key(record: ProfileUpdateRecord) -> tuple[str, str]:
    return record.timestamp, record.record_id


def profile_update_records_dir(repo_root: Path) -> Path:
    return repo_root / "records" / "profile-updates"


def prevent_duplicate_usernames_enabled(env: dict[str, str] | None = None) -> bool:
    return env_flag_enabled(PREVENT_DUPLICATE_USERNAMES_ENV, env=env)


def ensure_timestamp_text(timestamp_text: str) -> str:
    try:
        datetime.strptime(timestamp_text, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as exc:
        raise ValueError("Timestamp must use UTC ISO-8601 form YYYY-MM-DDTHH:MM:SSZ") from exc
    return timestamp_text


def normalize_display_name(display_name: str, *, strict_username: bool = False) -> str:
    value = display_name.strip()
    if not value:
        raise ValueError("display name must not be blank")
    if "\n" in value or "\r" in value:
        raise ValueError("display name must be a single line")
    try:
        value.encode("ascii")
    except UnicodeEncodeError as exc:
        raise ValueError("display name must be ASCII") from exc
    if strict_username:
        if len(value) < MIN_DISPLAY_NAME_LENGTH:
            raise ValueError(f"display name must be at least {MIN_DISPLAY_NAME_LENGTH} characters")
        if len(value) > MAX_DISPLAY_NAME_LENGTH:
            raise ValueError(f"display name must be at most {MAX_DISPLAY_NAME_LENGTH} characters")
        if DISPLAY_NAME_PATTERN.fullmatch(value) is None:
            raise ValueError(
                "display name must use lowercase ASCII letters, digits, and single hyphens only"
            )
        if value in RESERVED_DISPLAY_NAMES:
            raise ValueError("display name is reserved")
    elif len(value) > 80:
        raise ValueError("display name must be at most 80 characters")
    return value


def parse_profile_update_text(
    raw_text: str,
    *,
    source_path: Path | None = None,
    strict_username: bool = False,
) -> ProfileUpdateRecord:
    header_text, separator, body_text = raw_text.partition("\n\n")
    if not separator:
        raise ValueError("profile-update text is missing header/body separator")

    headers: dict[str, str] = {}
    for line in header_text.splitlines():
        if ": " not in line:
            raise ValueError(f"invalid profile-update header line: {line!r}")
        key, value = line.split(": ", 1)
        headers[key] = value.strip()

    record_id = headers.get("Record-ID")
    action = (headers.get("Action") or "").strip().lower()
    source_identity_id = headers.get("Source-Identity-ID")
    timestamp = headers.get("Timestamp")

    if not record_id or not action or not source_identity_id or not timestamp:
        raise ValueError("profile-update text is missing required headers")
    if action not in ALLOWED_PROFILE_UPDATE_ACTIONS:
        raise ValueError(f"unsupported profile-update action: {action}")

    return ProfileUpdateRecord(
        record_id=record_id,
        action=action,
        source_identity_id=ensure_identity_id_text(
            source_identity_id,
            field_name="Source-Identity-ID",
        ),
        timestamp=ensure_timestamp_text(timestamp),
        display_name=normalize_display_name(body_text.rstrip("\n"), strict_username=strict_username),
        path=source_path or Path("<request>"),
    )


def resolve_profile_update_signature_path(record_path: Path) -> Path | None:
    candidate = record_path.with_name(f"{record_path.name}.asc")
    return candidate if candidate.exists() else None


def resolve_profile_update_public_key_path(record_path: Path) -> Path | None:
    candidate = record_path.with_name(f"{record_path.name}.pub.asc")
    if candidate.exists():
        return candidate
    return resolve_public_key_from_signature(
        repo_root=record_path.parents[2],
        signature_path=resolve_profile_update_signature_path(record_path),
    )


def parse_profile_update_record(path: Path) -> ProfileUpdateRecord:
    record = parse_profile_update_text(path.read_text(encoding="ascii"), source_path=path)
    signature_path = resolve_profile_update_signature_path(path)
    public_key_path = resolve_profile_update_public_key_path(path)

    signer_fingerprint = None
    identity_id = None
    if public_key_path is not None:
        signer_fingerprint = fingerprint_from_public_key_path(public_key_path)
        identity_id = build_identity_id(signer_fingerprint)

    return ProfileUpdateRecord(
        record_id=record.record_id,
        action=record.action,
        source_identity_id=record.source_identity_id,
        timestamp=record.timestamp,
        display_name=record.display_name,
        path=record.path,
        signature_path=signature_path,
        public_key_path=public_key_path,
        signer_fingerprint=signer_fingerprint,
        identity_id=identity_id,
    )


def load_profile_update_records(records_dir: Path) -> list[ProfileUpdateRecord]:
    if not records_dir.exists():
        return []
    records = [parse_profile_update_record(path) for path in sorted(records_dir.glob("*.txt"))]
    return sorted(records, key=profile_update_sort_key)


def has_visible_profile_update_for_source_identity(
    *,
    source_identity_id: str,
    profile_updates: list[ProfileUpdateRecord],
    exclude_record_id: str | None = None,
) -> bool:
    return any(
        record.source_identity_id == source_identity_id
        and record.record_id != exclude_record_id
        for record in profile_updates
    )


def resolve_current_display_name(
    *,
    member_identity_ids: tuple[str, ...],
    profile_updates: list[ProfileUpdateRecord],
) -> ResolvedDisplayName | None:
    member_identity_id_set = frozenset(member_identity_ids)
    candidates = [
        record
        for record in profile_updates
        if record.source_identity_id in member_identity_id_set
    ]
    if not candidates:
        return None

    winner = max(candidates, key=profile_update_sort_key)
    return ResolvedDisplayName(
        display_name=winner.display_name,
        record_id=winner.record_id,
        source_identity_id=winner.source_identity_id,
        timestamp=winner.timestamp,
    )
