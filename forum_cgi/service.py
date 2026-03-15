from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from forum_cgi.posting import (
    PostingError,
    StoredArtifacts,
    build_preview,
    ensure_ascii_text,
    ensure_post_id_available,
    parse_payload,
    resolve_public_key_path,
    resolve_signature_path,
    store_post,
    validate_create_reply,
    validate_create_thread,
)
from forum_cgi.signing import verify_detached_signature


@dataclass(frozen=True)
class SubmissionResult:
    command_name: str
    record_id: str
    thread_id: str
    parent_id: str | None
    stored_path: str
    commit_id: str | None
    dry_run: bool
    signature_path: str | None = None
    public_key_path: str | None = None
    signer_fingerprint: str | None = None


def submit_create_thread(
    payload_text: str,
    repo_root: Path,
    *,
    dry_run: bool,
    signature_text: str | None = None,
    public_key_text: str | None = None,
    require_signature: bool = False,
) -> SubmissionResult:
    post = parse_payload(ensure_ascii_text(payload_text, field_name="payload"))
    validate_create_thread(post)
    return _submit_post(
        "create_thread",
        post=post,
        repo_root=repo_root,
        payload_text=payload_text,
        dry_run=dry_run,
        signature_text=signature_text,
        public_key_text=public_key_text,
        require_signature=require_signature,
    )


def submit_create_reply(
    payload_text: str,
    repo_root: Path,
    *,
    dry_run: bool,
    signature_text: str | None = None,
    public_key_text: str | None = None,
    require_signature: bool = False,
) -> SubmissionResult:
    post = parse_payload(ensure_ascii_text(payload_text, field_name="payload"))
    validate_create_reply(post, repo_root)
    return _submit_post(
        "create_reply",
        post=post,
        repo_root=repo_root,
        payload_text=payload_text,
        dry_run=dry_run,
        signature_text=signature_text,
        public_key_text=public_key_text,
        require_signature=require_signature,
    )


def _submit_post(
    command_name: str,
    *,
    post,
    repo_root: Path,
    payload_text: str,
    dry_run: bool,
    signature_text: str | None,
    public_key_text: str | None,
    require_signature: bool,
) -> SubmissionResult:
    signer_fingerprint = None
    signature_path = None
    public_key_path = None

    if require_signature and (signature_text is None or public_key_text is None):
        raise PostingError("bad_request", "signature and public_key are required")
    if signature_text is not None or public_key_text is not None:
        if not signature_text or not public_key_text:
            raise PostingError("bad_request", "signature and public_key must be provided together")
        signer_fingerprint = verify_detached_signature(
            payload_text=payload_text,
            signature_text=signature_text,
            public_key_text=public_key_text,
        )
        signature_path = str(resolve_signature_path(repo_root, post.post_id).relative_to(repo_root))
        public_key_path = str(resolve_public_key_path(repo_root, post.post_id).relative_to(repo_root))

    ensure_post_id_available(post, repo_root)

    if dry_run:
        preview = build_preview(command_name, post, repo_root)
        return SubmissionResult(
            command_name=command_name,
            record_id=preview.record_id,
            thread_id=preview.thread_id,
            parent_id=preview.parent_id,
            stored_path=preview.stored_path,
            commit_id=None,
            dry_run=True,
            signature_path=signature_path,
            public_key_path=public_key_path,
            signer_fingerprint=signer_fingerprint,
        )

    commit_id, artifacts = store_post(
        command_name,
        post,
        repo_root,
        payload_text,
        signature_text=signature_text,
        public_key_text=public_key_text,
    )
    return SubmissionResult(
        command_name=command_name,
        record_id=post.post_id,
        thread_id=post.root_thread_id,
        parent_id=post.parent_id,
        stored_path=artifacts.post_path,
        commit_id=commit_id,
        dry_run=False,
        signature_path=artifacts.signature_path,
        public_key_path=artifacts.public_key_path,
        signer_fingerprint=signer_fingerprint,
    )
