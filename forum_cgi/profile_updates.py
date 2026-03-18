from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from forum_core.identity import build_identity_id
from forum_core.profile_updates import (
    ProfileUpdateRecord,
    parse_profile_update_text,
    profile_update_records_dir,
)
from forum_core.public_keys import resolve_canonical_public_key_path, store_or_reuse_public_key
from forum_cgi.posting import (
    PostingError,
    build_commit_message,
    commit_post,
    ensure_ascii_text,
    records_dir,
    write_ascii_file,
)
from forum_cgi.signing import verify_detached_signature
from forum_web.profiles import load_identity_context
from forum_web.repository import load_posts


@dataclass(frozen=True)
class ProfileUpdateSubmissionResult:
    command_name: str
    record_id: str
    action: str
    source_identity_id: str
    timestamp: str
    display_name: str
    stored_path: str
    commit_id: str | None
    dry_run: bool
    signature_path: str | None = None
    public_key_path: str | None = None
    signer_fingerprint: str | None = None
    identity_id: str | None = None


def resolve_profile_update_path(repo_root: Path, record_id: str) -> Path:
    return profile_update_records_dir(repo_root) / f"{record_id}.txt"


def resolve_profile_update_signature_path(repo_root: Path, record_id: str) -> Path:
    return profile_update_records_dir(repo_root) / f"{record_id}.txt.asc"


def parse_profile_update_payload(payload_text: str) -> ProfileUpdateRecord:
    try:
        return parse_profile_update_text(payload_text)
    except ValueError as exc:
        raise PostingError("bad_request", str(exc)) from exc


def ensure_profile_update_record_id_available(record: ProfileUpdateRecord, repo_root: Path) -> None:
    if resolve_profile_update_path(repo_root, record.record_id).exists():
        raise PostingError(
            "conflict",
            f"profile-update record already exists: {record.record_id}",
            status="409 Conflict",
        )


def validate_profile_update_record(
    record: ProfileUpdateRecord,
    repo_root: Path,
    *,
    signer_identity_id: str,
) -> None:
    posts = load_posts(records_dir(repo_root))
    identity_context = load_identity_context(repo_root=repo_root, posts=posts)

    if signer_identity_id != record.source_identity_id:
        raise PostingError("forbidden", "signer must match Source-Identity-ID", status="403 Forbidden")
    if identity_context.canonical_identity_id(record.source_identity_id) is None:
        raise PostingError(
            "not_found",
            f"unknown source identity: {record.source_identity_id}",
            status="404 Not Found",
        )


def build_profile_update_preview(record: ProfileUpdateRecord, repo_root: Path) -> ProfileUpdateSubmissionResult:
    return ProfileUpdateSubmissionResult(
        command_name="update_profile",
        record_id=record.record_id,
        action=record.action,
        source_identity_id=record.source_identity_id,
        timestamp=record.timestamp,
        display_name=record.display_name,
        stored_path=str(resolve_profile_update_path(repo_root, record.record_id).relative_to(repo_root)),
        commit_id=None,
        dry_run=True,
    )


def store_profile_update_record(
    record: ProfileUpdateRecord,
    repo_root: Path,
    payload_text: str,
    *,
    signature_text: str,
    public_key_text: str,
) -> tuple[str, str, str, str]:
    records_path = profile_update_records_dir(repo_root)
    records_path.mkdir(parents=True, exist_ok=True)
    record_path = write_ascii_file(
        resolve_profile_update_path(repo_root, record.record_id),
        ensure_ascii_text(payload_text, field_name="payload"),
    )
    signature_path = write_ascii_file(
        resolve_profile_update_signature_path(repo_root, record.record_id),
        ensure_ascii_text(signature_text, field_name="signature"),
    )
    stored_public_key = store_or_reuse_public_key(
        repo_root=repo_root,
        public_key_text=ensure_ascii_text(public_key_text, field_name="public_key"),
    )
    public_key_path = stored_public_key.path
    commit_id = commit_post(
        repo_root,
        [record_path, signature_path, *([public_key_path] if stored_public_key.created else [])],
        message=build_commit_message("update_profile", record.record_id),
    )
    return (
        commit_id,
        str(record_path.relative_to(repo_root)),
        str(signature_path.relative_to(repo_root)),
        str(public_key_path.relative_to(repo_root)),
    )


def submit_profile_update(
    payload_text: str,
    repo_root: Path,
    *,
    dry_run: bool,
    signature_text: str | None = None,
    public_key_text: str | None = None,
    require_signature: bool = True,
) -> ProfileUpdateSubmissionResult:
    payload_text = ensure_ascii_text(payload_text, field_name="payload")
    record = parse_profile_update_payload(payload_text)

    if require_signature and (signature_text is None or public_key_text is None):
        raise PostingError("bad_request", "signature and public_key are required")
    if not signature_text or not public_key_text:
        raise PostingError("bad_request", "signature and public_key must be provided together")

    signer_fingerprint = verify_detached_signature(
        payload_text=payload_text,
        signature_text=signature_text,
        public_key_text=public_key_text,
    )
    signer_identity_id = build_identity_id(signer_fingerprint)

    validate_profile_update_record(record, repo_root, signer_identity_id=signer_identity_id)
    ensure_profile_update_record_id_available(record, repo_root)

    signature_path = str(
        resolve_profile_update_signature_path(repo_root, record.record_id).relative_to(repo_root)
    )
    public_key_path = str(resolve_canonical_public_key_path(repo_root, signer_fingerprint).relative_to(repo_root))

    if dry_run:
        preview = build_profile_update_preview(record, repo_root)
        return ProfileUpdateSubmissionResult(
            command_name=preview.command_name,
            record_id=preview.record_id,
            action=preview.action,
            source_identity_id=preview.source_identity_id,
            timestamp=preview.timestamp,
            display_name=preview.display_name,
            stored_path=preview.stored_path,
            commit_id=None,
            dry_run=True,
            signature_path=signature_path,
            public_key_path=public_key_path,
            signer_fingerprint=signer_fingerprint,
            identity_id=signer_identity_id,
        )

    commit_id, stored_path, stored_signature_path, stored_public_key_path = store_profile_update_record(
        record,
        repo_root,
        payload_text,
        signature_text=signature_text,
        public_key_text=public_key_text,
    )
    return ProfileUpdateSubmissionResult(
        command_name="update_profile",
        record_id=record.record_id,
        action=record.action,
        source_identity_id=record.source_identity_id,
        timestamp=record.timestamp,
        display_name=record.display_name,
        stored_path=stored_path,
        commit_id=commit_id,
        dry_run=False,
        signature_path=stored_signature_path,
        public_key_path=stored_public_key_path,
        signer_fingerprint=signer_fingerprint,
        identity_id=signer_identity_id,
    )
