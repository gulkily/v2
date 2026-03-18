from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from forum_core.identity import build_identity_id, load_identity_bootstraps
from forum_core.merge_requests import (
    MergeRequestRecord,
    derive_merge_request_states,
    load_merge_request_records,
    merge_request_records_dir,
    parse_merge_request_text,
)
from forum_core.moderation import is_authorized_moderator
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
class MergeRequestSubmissionResult:
    command_name: str
    record_id: str
    action: str
    requester_identity_id: str
    target_identity_id: str
    actor_identity_id: str
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


def resolve_merge_request_path(repo_root: Path, record_id: str) -> Path:
    return merge_request_records_dir(repo_root) / f"{record_id}.txt"


def resolve_merge_request_signature_path(repo_root: Path, record_id: str) -> Path:
    return merge_request_records_dir(repo_root) / f"{record_id}.txt.asc"


def resolve_merge_request_public_key_path(repo_root: Path, record_id: str) -> Path:
    return merge_request_records_dir(repo_root) / f"{record_id}.txt.pub.asc"


def parse_merge_request_payload(payload_text: str) -> MergeRequestRecord:
    try:
        return parse_merge_request_text(payload_text)
    except ValueError as exc:
        raise PostingError("bad_request", str(exc)) from exc


def ensure_merge_request_record_id_available(record: MergeRequestRecord, repo_root: Path) -> None:
    if resolve_merge_request_path(repo_root, record.record_id).exists():
        raise PostingError("conflict", f"merge-request record already exists: {record.record_id}", status="409 Conflict")


def load_visible_identity_ids(repo_root: Path) -> frozenset[str]:
    posts = load_posts(records_dir(repo_root))
    bootstraps = load_identity_bootstraps(identity_records_dir(repo_root))
    return frozenset(
        identity_id
        for identity_id in [bootstrap.identity_id for bootstrap in bootstraps] + [post.identity_id or "" for post in posts]
        if identity_id
    )


def load_pending_state(repo_root: Path, *, requester_identity_id: str, target_identity_id: str):
    states = derive_merge_request_states(load_merge_request_records(merge_request_records_dir(repo_root)))
    for state in states:
        if state.requester_identity_id == requester_identity_id and state.target_identity_id == target_identity_id:
            return state
    return None


def validate_merge_request_record(
    record: MergeRequestRecord,
    repo_root: Path,
    *,
    signer_identity_id: str,
    signer_fingerprint: str,
) -> None:
    visible_identity_ids = load_visible_identity_ids(repo_root)
    posts = load_posts(records_dir(repo_root))
    identity_context = load_identity_context(repo_root=repo_root, posts=posts)

    if record.requester_identity_id not in visible_identity_ids:
        raise PostingError("not_found", f"unknown requester identity: {record.requester_identity_id}", status="404 Not Found")
    if record.target_identity_id not in visible_identity_ids:
        raise PostingError("not_found", f"unknown target identity: {record.target_identity_id}", status="404 Not Found")
    requester_canonical_identity_id = identity_context.canonical_identity_id(record.requester_identity_id)
    target_canonical_identity_id = identity_context.canonical_identity_id(record.target_identity_id)

    if record.action == "request_merge":
        if requester_canonical_identity_id == target_canonical_identity_id:
            raise PostingError("conflict", "identities already resolve together", status="409 Conflict")
        if signer_identity_id != record.requester_identity_id or record.actor_identity_id != signer_identity_id:
            raise PostingError("forbidden", "request signer must match Requester-Identity-ID and Actor-Identity-ID", status="403 Forbidden")
        return

    pending_state = load_pending_state(
        repo_root,
        requester_identity_id=record.requester_identity_id,
        target_identity_id=record.target_identity_id,
    )
    if record.action in {"approve_merge", "dismiss_merge"}:
        if pending_state is None or not pending_state.pending:
            raise PostingError("conflict", "no pending merge request exists for this identity pair", status="409 Conflict")
        target_canonical_identity_id = identity_context.canonical_identity_id(record.target_identity_id)
        signer_canonical_identity_id = identity_context.canonical_identity_id(signer_identity_id)
        if (
            signer_canonical_identity_id != target_canonical_identity_id
            or record.actor_identity_id != signer_identity_id
        ):
            raise PostingError(
                "forbidden",
                "response signer must belong to the Target-Identity-ID resolved set and match Actor-Identity-ID",
                status="403 Forbidden",
            )
        return

    if record.action == "revoke_merge":
        if pending_state is None:
            raise PostingError("conflict", "no merge request exists for this identity pair", status="409 Conflict")
        if not pending_state.active_merge:
            raise PostingError("conflict", "no active merge exists for this identity pair", status="409 Conflict")
        signer_canonical_identity_id = identity_context.canonical_identity_id(signer_identity_id)
        if (
            signer_canonical_identity_id not in {requester_canonical_identity_id, target_canonical_identity_id}
            or record.actor_identity_id != signer_identity_id
        ):
            raise PostingError(
                "forbidden",
                "revoke signer must belong to the merged resolved set and match Actor-Identity-ID",
                status="403 Forbidden",
            )
        return

    if not is_authorized_moderator(signer_fingerprint):
        raise PostingError("forbidden", "signer is not an authorized moderator", status="403 Forbidden")
    if record.actor_identity_id != signer_identity_id:
        raise PostingError("forbidden", "moderator signer must match Actor-Identity-ID", status="403 Forbidden")


def build_merge_request_preview(record: MergeRequestRecord, repo_root: Path) -> MergeRequestSubmissionResult:
    return MergeRequestSubmissionResult(
        command_name="merge_request",
        record_id=record.record_id,
        action=record.action,
        requester_identity_id=record.requester_identity_id,
        target_identity_id=record.target_identity_id,
        actor_identity_id=record.actor_identity_id,
        timestamp=record.timestamp,
        stored_path=str(resolve_merge_request_path(repo_root, record.record_id).relative_to(repo_root)),
        commit_id=None,
        dry_run=True,
    )


def store_merge_request_record(
    record: MergeRequestRecord,
    repo_root: Path,
    payload_text: str,
    *,
    signature_text: str,
    public_key_text: str,
) -> tuple[str, str, str, str]:
    merge_dir = merge_request_records_dir(repo_root)
    merge_dir.mkdir(parents=True, exist_ok=True)
    record_path = write_ascii_file(
        resolve_merge_request_path(repo_root, record.record_id),
        ensure_ascii_text(payload_text, field_name="payload"),
    )
    signature_path = write_ascii_file(
        resolve_merge_request_signature_path(repo_root, record.record_id),
        ensure_ascii_text(signature_text, field_name="signature"),
    )
    public_key_path = write_ascii_file(
        resolve_merge_request_public_key_path(repo_root, record.record_id),
        ensure_ascii_text(public_key_text, field_name="public_key"),
    )
    commit_id = commit_post(
        repo_root,
        [record_path, signature_path, public_key_path],
        message=build_commit_message("merge_request", record.record_id),
    )
    return (
        commit_id,
        str(record_path.relative_to(repo_root)),
        str(signature_path.relative_to(repo_root)),
        str(public_key_path.relative_to(repo_root)),
    )


def submit_merge_request(
    payload_text: str,
    repo_root: Path,
    *,
    dry_run: bool,
    signature_text: str | None = None,
    public_key_text: str | None = None,
    require_signature: bool = True,
) -> MergeRequestSubmissionResult:
    payload_text = ensure_ascii_text(payload_text, field_name="payload")
    record = parse_merge_request_payload(payload_text)

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

    validate_merge_request_record(
        record,
        repo_root,
        signer_identity_id=signer_identity_id,
        signer_fingerprint=signer_fingerprint,
    )
    ensure_merge_request_record_id_available(record, repo_root)

    signature_path = str(resolve_merge_request_signature_path(repo_root, record.record_id).relative_to(repo_root))
    public_key_path = str(resolve_merge_request_public_key_path(repo_root, record.record_id).relative_to(repo_root))

    if dry_run:
        preview = build_merge_request_preview(record, repo_root)
        return MergeRequestSubmissionResult(
            command_name=preview.command_name,
            record_id=preview.record_id,
            action=preview.action,
            requester_identity_id=preview.requester_identity_id,
            target_identity_id=preview.target_identity_id,
            actor_identity_id=preview.actor_identity_id,
            timestamp=preview.timestamp,
            stored_path=preview.stored_path,
            commit_id=None,
            dry_run=True,
            signature_path=signature_path,
            public_key_path=public_key_path,
            signer_fingerprint=signer_fingerprint,
            identity_id=signer_identity_id,
        )

    commit_id, stored_path, stored_signature_path, stored_public_key_path = store_merge_request_record(
        record,
        repo_root,
        payload_text,
        signature_text=signature_text,
        public_key_text=public_key_text,
    )
    return MergeRequestSubmissionResult(
        command_name="merge_request",
        record_id=record.record_id,
        action=record.action,
        requester_identity_id=record.requester_identity_id,
        target_identity_id=record.target_identity_id,
        actor_identity_id=record.actor_identity_id,
        timestamp=record.timestamp,
        stored_path=stored_path,
        commit_id=commit_id,
        dry_run=False,
        signature_path=stored_signature_path,
        public_key_path=stored_public_key_path,
        signer_fingerprint=signer_fingerprint,
        identity_id=signer_identity_id,
    )
