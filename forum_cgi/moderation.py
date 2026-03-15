from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from forum_core.identity import build_identity_id
from forum_core.moderation import (
    ModerationRecord,
    is_authorized_moderator,
    moderation_records_dir,
    parse_moderation_text,
)
from forum_cgi.posting import (
    PostingError,
    build_commit_message,
    commit_post,
    ensure_ascii_text,
    records_dir,
    write_ascii_file,
)
from forum_cgi.signing import verify_detached_signature
from forum_read_only.repository import index_posts, load_posts


@dataclass(frozen=True)
class ModerationSubmissionResult:
    command_name: str
    record_id: str
    action: str
    target_type: str
    target_id: str
    timestamp: str
    stored_path: str
    commit_id: str | None
    dry_run: bool
    signature_path: str | None = None
    public_key_path: str | None = None
    signer_fingerprint: str | None = None
    identity_id: str | None = None

def resolve_moderation_path(repo_root: Path, record_id: str) -> Path:
    return moderation_records_dir(repo_root) / f"{record_id}.txt"


def resolve_moderation_signature_path(repo_root: Path, record_id: str) -> Path:
    return moderation_records_dir(repo_root) / f"{record_id}.txt.asc"


def resolve_moderation_public_key_path(repo_root: Path, record_id: str) -> Path:
    return moderation_records_dir(repo_root) / f"{record_id}.txt.pub.asc"


def parse_moderation_payload(payload_text: str) -> ModerationRecord:
    try:
        return parse_moderation_text(payload_text)
    except ValueError as exc:
        raise PostingError("bad_request", str(exc)) from exc


def ensure_moderation_record_id_available(record: ModerationRecord, repo_root: Path) -> None:
    if resolve_moderation_path(repo_root, record.record_id).exists():
        raise PostingError("conflict", f"moderation record already exists: {record.record_id}", status="409 Conflict")


def validate_moderation_target(record: ModerationRecord, repo_root: Path) -> None:
    posts = load_posts(records_dir(repo_root))
    posts_by_id = index_posts(posts)

    if record.target_type == "post":
        if posts_by_id.get(record.target_id) is None:
            raise PostingError("not_found", f"unknown post: {record.target_id}", status="404 Not Found")
        return

    target_thread = posts_by_id.get(record.target_id)
    if target_thread is None or not target_thread.is_root:
        raise PostingError("not_found", f"unknown thread: {record.target_id}", status="404 Not Found")


def build_moderation_preview(record: ModerationRecord, repo_root: Path) -> ModerationSubmissionResult:
    return ModerationSubmissionResult(
        command_name="moderate",
        record_id=record.record_id,
        action=record.action,
        target_type=record.target_type,
        target_id=record.target_id,
        timestamp=record.timestamp,
        stored_path=str(resolve_moderation_path(repo_root, record.record_id).relative_to(repo_root)),
        commit_id=None,
        dry_run=True,
    )


def store_moderation_record(
    record: ModerationRecord,
    repo_root: Path,
    payload_text: str,
    *,
    signature_text: str,
    public_key_text: str,
) -> tuple[str, str, str, str]:
    moderation_dir = moderation_records_dir(repo_root)
    moderation_dir.mkdir(parents=True, exist_ok=True)
    record_path = write_ascii_file(
        resolve_moderation_path(repo_root, record.record_id),
        ensure_ascii_text(payload_text, field_name="payload"),
    )
    signature_path = write_ascii_file(
        resolve_moderation_signature_path(repo_root, record.record_id),
        ensure_ascii_text(signature_text, field_name="signature"),
    )
    public_key_path = write_ascii_file(
        resolve_moderation_public_key_path(repo_root, record.record_id),
        ensure_ascii_text(public_key_text, field_name="public_key"),
    )
    commit_id = commit_post(
        repo_root,
        [record_path, signature_path, public_key_path],
        message=build_commit_message("moderate", record.record_id),
    )
    return (
        commit_id,
        str(record_path.relative_to(repo_root)),
        str(signature_path.relative_to(repo_root)),
        str(public_key_path.relative_to(repo_root)),
    )


def submit_moderation(
    payload_text: str,
    repo_root: Path,
    *,
    dry_run: bool,
    signature_text: str | None = None,
    public_key_text: str | None = None,
    require_signature: bool = True,
) -> ModerationSubmissionResult:
    payload_text = ensure_ascii_text(payload_text, field_name="payload")
    record = parse_moderation_payload(payload_text)

    if require_signature and (signature_text is None or public_key_text is None):
        raise PostingError("bad_request", "signature and public_key are required")
    if not signature_text or not public_key_text:
        raise PostingError("bad_request", "signature and public_key must be provided together")

    signer_fingerprint = verify_detached_signature(
        payload_text=payload_text,
        signature_text=signature_text,
        public_key_text=public_key_text,
    )
    if not is_authorized_moderator(signer_fingerprint):
        raise PostingError("forbidden", "signer is not an authorized moderator", status="403 Forbidden")

    validate_moderation_target(record, repo_root)
    ensure_moderation_record_id_available(record, repo_root)

    identity_id = build_identity_id(signer_fingerprint)
    signature_path = str(resolve_moderation_signature_path(repo_root, record.record_id).relative_to(repo_root))
    public_key_path = str(resolve_moderation_public_key_path(repo_root, record.record_id).relative_to(repo_root))

    if dry_run:
        preview = build_moderation_preview(record, repo_root)
        return ModerationSubmissionResult(
            command_name=preview.command_name,
            record_id=preview.record_id,
            action=preview.action,
            target_type=preview.target_type,
            target_id=preview.target_id,
            timestamp=preview.timestamp,
            stored_path=preview.stored_path,
            commit_id=None,
            dry_run=True,
            signature_path=signature_path,
            public_key_path=public_key_path,
            signer_fingerprint=signer_fingerprint,
            identity_id=identity_id,
        )

    commit_id, stored_path, stored_signature_path, stored_public_key_path = store_moderation_record(
        record,
        repo_root,
        payload_text,
        signature_text=signature_text,
        public_key_text=public_key_text,
    )
    return ModerationSubmissionResult(
        command_name="moderate",
        record_id=record.record_id,
        action=record.action,
        target_type=record.target_type,
        target_id=record.target_id,
        timestamp=record.timestamp,
        stored_path=stored_path,
        commit_id=commit_id,
        dry_run=False,
        signature_path=stored_signature_path,
        public_key_path=stored_public_key_path,
        signer_fingerprint=signer_fingerprint,
        identity_id=identity_id,
    )
