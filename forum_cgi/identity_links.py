from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from forum_core.identity import build_identity_id, load_identity_bootstraps
from forum_core.identity_links import (
    IdentityLinkRecord,
    collect_visible_identity_ids,
    identity_link_records_dir,
    load_identity_link_records,
    parse_identity_link_text,
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
from forum_web.repository import load_posts


@dataclass(frozen=True)
class IdentityLinkSubmissionResult:
    command_name: str
    record_id: str
    action: str
    source_identity_id: str
    target_identity_id: str
    timestamp: str
    stored_path: str
    commit_id: str | None
    dry_run: bool
    signature_path: str | None = None
    public_key_path: str | None = None
    signer_fingerprint: str | None = None
    identity_id: str | None = None


def identity_records_dir(repo_root: Path) -> Path:
    return repo_root / "records" / "identity"


def resolve_identity_link_path(repo_root: Path, record_id: str) -> Path:
    return identity_link_records_dir(repo_root) / f"{record_id}.txt"


def resolve_identity_link_signature_path(repo_root: Path, record_id: str) -> Path:
    return identity_link_records_dir(repo_root) / f"{record_id}.txt.asc"


def resolve_identity_link_public_key_path(repo_root: Path, record_id: str) -> Path:
    return identity_link_records_dir(repo_root) / f"{record_id}.txt.pub.asc"


def parse_identity_link_payload(payload_text: str) -> IdentityLinkRecord:
    try:
        return parse_identity_link_text(payload_text)
    except ValueError as exc:
        raise PostingError("bad_request", str(exc)) from exc


def ensure_identity_link_record_id_available(record: IdentityLinkRecord, repo_root: Path) -> None:
    if resolve_identity_link_path(repo_root, record.record_id).exists():
        raise PostingError("conflict", f"identity-link record already exists: {record.record_id}", status="409 Conflict")


def load_visible_identity_ids(repo_root: Path) -> frozenset[str]:
    posts = load_posts(records_dir(repo_root))
    bootstraps = load_identity_bootstraps(identity_records_dir(repo_root))
    return collect_visible_identity_ids(
        identity_bootstrap_ids=[bootstrap.identity_id for bootstrap in bootstraps],
        post_identity_ids=[post.identity_id or "" for post in posts],
    )


def referenced_identity_ids(link_records: list[IdentityLinkRecord]) -> frozenset[str]:
    return frozenset(
        identity_id
        for record in link_records
        for identity_id in (record.source_identity_id, record.target_identity_id)
    )


def validate_identity_link_record(
    record: IdentityLinkRecord,
    repo_root: Path,
    *,
    signer_identity_id: str,
) -> None:
    visible_identity_ids = load_visible_identity_ids(repo_root)
    if signer_identity_id != record.source_identity_id:
        raise PostingError("forbidden", "signer must match Source-Identity-ID", status="403 Forbidden")
    if record.source_identity_id not in visible_identity_ids:
        raise PostingError("not_found", f"unknown source identity: {record.source_identity_id}", status="404 Not Found")

    existing_link_records = load_identity_link_records(identity_link_records_dir(repo_root))
    known_link_identity_ids = referenced_identity_ids(existing_link_records)

    if record.action == "merge_identity":
        if record.target_identity_id not in visible_identity_ids:
            raise PostingError("not_found", f"unknown target identity: {record.target_identity_id}", status="404 Not Found")
        return

    if record.target_identity_id in visible_identity_ids or record.target_identity_id in known_link_identity_ids:
        raise PostingError("conflict", f"target identity already exists: {record.target_identity_id}", status="409 Conflict")


def build_identity_link_preview(record: IdentityLinkRecord, repo_root: Path) -> IdentityLinkSubmissionResult:
    return IdentityLinkSubmissionResult(
        command_name="link_identity",
        record_id=record.record_id,
        action=record.action,
        source_identity_id=record.source_identity_id,
        target_identity_id=record.target_identity_id,
        timestamp=record.timestamp,
        stored_path=str(resolve_identity_link_path(repo_root, record.record_id).relative_to(repo_root)),
        commit_id=None,
        dry_run=True,
    )


def store_identity_link_record(
    record: IdentityLinkRecord,
    repo_root: Path,
    payload_text: str,
    *,
    signature_text: str,
    public_key_text: str,
) -> tuple[str, str, str, str]:
    records_path = identity_link_records_dir(repo_root)
    records_path.mkdir(parents=True, exist_ok=True)
    record_path = write_ascii_file(
        resolve_identity_link_path(repo_root, record.record_id),
        ensure_ascii_text(payload_text, field_name="payload"),
    )
    signature_path = write_ascii_file(
        resolve_identity_link_signature_path(repo_root, record.record_id),
        ensure_ascii_text(signature_text, field_name="signature"),
    )
    public_key_path = write_ascii_file(
        resolve_identity_link_public_key_path(repo_root, record.record_id),
        ensure_ascii_text(public_key_text, field_name="public_key"),
    )
    commit_id = commit_post(
        repo_root,
        [record_path, signature_path, public_key_path],
        message=build_commit_message("link_identity", record.record_id),
    )
    return (
        commit_id,
        str(record_path.relative_to(repo_root)),
        str(signature_path.relative_to(repo_root)),
        str(public_key_path.relative_to(repo_root)),
    )


def submit_identity_link(
    payload_text: str,
    repo_root: Path,
    *,
    dry_run: bool,
    signature_text: str | None = None,
    public_key_text: str | None = None,
    require_signature: bool = True,
) -> IdentityLinkSubmissionResult:
    payload_text = ensure_ascii_text(payload_text, field_name="payload")
    record = parse_identity_link_payload(payload_text)

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

    validate_identity_link_record(record, repo_root, signer_identity_id=signer_identity_id)
    ensure_identity_link_record_id_available(record, repo_root)

    signature_path = str(resolve_identity_link_signature_path(repo_root, record.record_id).relative_to(repo_root))
    public_key_path = str(resolve_identity_link_public_key_path(repo_root, record.record_id).relative_to(repo_root))

    if dry_run:
        preview = build_identity_link_preview(record, repo_root)
        return IdentityLinkSubmissionResult(
            command_name=preview.command_name,
            record_id=preview.record_id,
            action=preview.action,
            source_identity_id=preview.source_identity_id,
            target_identity_id=preview.target_identity_id,
            timestamp=preview.timestamp,
            stored_path=preview.stored_path,
            commit_id=None,
            dry_run=True,
            signature_path=signature_path,
            public_key_path=public_key_path,
            signer_fingerprint=signer_fingerprint,
            identity_id=signer_identity_id,
        )

    commit_id, stored_path, stored_signature_path, stored_public_key_path = store_identity_link_record(
        record,
        repo_root,
        payload_text,
        signature_text=signature_text,
        public_key_text=public_key_text,
    )
    return IdentityLinkSubmissionResult(
        command_name="link_identity",
        record_id=record.record_id,
        action=record.action,
        source_identity_id=record.source_identity_id,
        target_identity_id=record.target_identity_id,
        timestamp=record.timestamp,
        stored_path=stored_path,
        commit_id=commit_id,
        dry_run=False,
        signature_path=stored_signature_path,
        public_key_path=stored_public_key_path,
        signer_fingerprint=signer_fingerprint,
        identity_id=signer_identity_id,
    )
