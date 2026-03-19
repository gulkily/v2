from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from pathlib import Path

from forum_cgi.auto_reply import AutoReplyError, generate_thread_auto_reply, thread_auto_reply_enabled
from forum_core.identity import build_bootstrap_payload, build_identity_id
from forum_core.llm_provider import LLMProviderError
from forum_core.public_keys import resolve_canonical_public_key_path
from forum_core.proof_of_work import (
    first_post_pow_difficulty,
    first_post_pow_enabled,
    pow_required_for_signed_post,
    verify_first_post_pow_stamp,
)
from forum_cgi.posting import (
    PostingError,
    StoredArtifacts,
    build_preview,
    ensure_ascii_text,
    ensure_post_id_available,
    parse_payload,
    resolve_identity_bootstrap_path,
    resolve_signature_path,
    store_post,
    validate_create_reply,
    validate_create_thread,
)
from forum_cgi.signing import verify_detached_signature
from forum_core.operation_events import emit_operation_timing

logger = logging.getLogger(__name__)


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
    identity_id: str | None = None
    identity_bootstrap_path: str | None = None
    identity_bootstrap_created: bool | None = None
    auto_reply_status: str | None = None
    auto_reply_record_id: str | None = None
    auto_reply_message: str | None = None
    auto_reply_model: str | None = None


def submit_create_thread(
    payload_text: str,
    repo_root: Path,
    *,
    dry_run: bool,
    signature_text: str | None = None,
    public_key_text: str | None = None,
    require_signature: bool = False,
) -> SubmissionResult:
    timing_measurements: list[tuple[str, float]] = []

    def record_timing(phase_name: str, duration_ms: float) -> None:
        timing_measurements.append((phase_name, duration_ms))

    started_at = time.perf_counter()
    post = parse_payload(ensure_ascii_text(payload_text, field_name="payload"))
    validate_create_thread(post)
    emit_operation_timing(record_timing, "parse_and_validate_thread", (time.perf_counter() - started_at) * 1000.0)
    started_at = time.perf_counter()
    result = _submit_post(
        "create_thread",
        post=post,
        repo_root=repo_root,
        payload_text=payload_text,
        dry_run=dry_run,
        signature_text=signature_text,
        public_key_text=public_key_text,
        require_signature=require_signature,
        timing_callback=record_timing,
    )
    emit_operation_timing(record_timing, "submit_post", (time.perf_counter() - started_at) * 1000.0)
    started_at = time.perf_counter()
    final_result = maybe_create_thread_auto_reply(post=post, repo_root=repo_root, dry_run=dry_run, result=result)
    emit_operation_timing(record_timing, "auto_reply", (time.perf_counter() - started_at) * 1000.0)
    logger.info(
        "create_thread timings for %s: %s",
        post.post_id,
        ", ".join(f"{phase_name}={duration_ms:.2f}ms" for phase_name, duration_ms in timing_measurements),
    )
    return final_result


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
    timing_callback=None,
) -> SubmissionResult:
    signer_fingerprint = None
    signature_path = None
    public_key_path = None
    identity_id = None
    identity_bootstrap_path = None
    identity_bootstrap_created = None
    identity_bootstrap_text = None

    if require_signature and (signature_text is None or public_key_text is None):
        raise PostingError("bad_request", "signature and public_key are required")
    if signature_text is not None or public_key_text is not None:
        if not signature_text or not public_key_text:
            raise PostingError("bad_request", "signature and public_key must be provided together")
        started_at = time.perf_counter()
        signer_fingerprint = verify_detached_signature(
            payload_text=payload_text,
            signature_text=signature_text,
            public_key_text=public_key_text,
        )
        emit_operation_timing(timing_callback, "verify_detached_signature", (time.perf_counter() - started_at) * 1000.0)
        identity_id = build_identity_id(signer_fingerprint)
        signature_path = str(resolve_signature_path(repo_root, post.post_id).relative_to(repo_root))
        public_key_path = str(resolve_canonical_public_key_path(repo_root, signer_fingerprint).relative_to(repo_root))
        bootstrap_path = resolve_identity_bootstrap_path(repo_root, identity_id)
        identity_bootstrap_path = str(bootstrap_path.relative_to(repo_root))
        identity_bootstrap_created = not bootstrap_path.exists()
        if identity_bootstrap_created:
            _, identity_bootstrap_text = build_bootstrap_payload(
                identity_id=identity_id,
                signer_fingerprint=signer_fingerprint,
                bootstrap_post_id=post.post_id,
                bootstrap_thread_id=post.root_thread_id,
                public_key_text=public_key_text,
            )
        if first_post_pow_enabled() and pow_required_for_signed_post(
            repo_root=repo_root,
            signer_fingerprint=signer_fingerprint,
        ):
            try:
                started_at = time.perf_counter()
                verify_first_post_pow_stamp(
                    payload_text=payload_text,
                    signer_fingerprint=signer_fingerprint,
                    difficulty=first_post_pow_difficulty(),
                )
                emit_operation_timing(timing_callback, "verify_first_post_pow", (time.perf_counter() - started_at) * 1000.0)
            except ValueError as exc:
                raise PostingError("bad_request", str(exc)) from exc

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
            identity_id=identity_id,
            identity_bootstrap_path=identity_bootstrap_path,
            identity_bootstrap_created=identity_bootstrap_created,
        )

    commit_id, artifacts = store_post(
        command_name,
        post,
        repo_root,
        payload_text,
        signature_text=signature_text,
        public_key_text=public_key_text,
        signer_fingerprint=signer_fingerprint,
        identity_bootstrap_path=(
            resolve_identity_bootstrap_path(repo_root, identity_id)
            if identity_bootstrap_created and identity_id and identity_bootstrap_text
            else None
        ),
        identity_bootstrap_text=identity_bootstrap_text,
        timing_callback=timing_callback,
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
        identity_id=identity_id,
        identity_bootstrap_path=artifacts.identity_bootstrap_path or identity_bootstrap_path,
        identity_bootstrap_created=identity_bootstrap_created,
    )


def maybe_create_thread_auto_reply(
    *,
    post,
    repo_root: Path,
    dry_run: bool,
    result: SubmissionResult,
) -> SubmissionResult:
    if dry_run:
        return _with_auto_reply(result, status="not_attempted", message="dry run")
    if not thread_auto_reply_enabled():
        return _with_auto_reply(result, status="disabled")

    try:
        auto_reply = generate_thread_auto_reply(thread_post=post, repo_root=repo_root)
        reply_result = submit_create_reply(
            auto_reply.payload_text,
            repo_root,
            dry_run=False,
            signature_text=auto_reply.signature_text,
            public_key_text=auto_reply.public_key_text,
            require_signature=auto_reply.signature_text is not None,
        )
    except (AutoReplyError, LLMProviderError, PostingError) as exc:
        logger.warning("Thread auto reply failed for %s: %s", post.post_id, exc)
        return _with_auto_reply(result, status="failed", message=str(exc))
    except Exception:
        logger.exception("Thread auto reply crashed for %s", post.post_id)
        return _with_auto_reply(result, status="failed", message="unexpected auto reply failure")

    if auto_reply.signing_mode == "unsigned":
        logger.warning("Thread auto reply for %s proceeded without signing: %s", post.post_id, auto_reply.status_message)
        return _with_auto_reply(
            result,
            status="created_unsigned",
            record_id=reply_result.record_id,
            message=auto_reply.status_message,
            model=auto_reply.model,
        )

    return _with_auto_reply(
        result,
        status="created",
        record_id=reply_result.record_id,
        model=auto_reply.model,
    )


def _with_auto_reply(
    result: SubmissionResult,
    *,
    status: str,
    record_id: str | None = None,
    message: str | None = None,
    model: str | None = None,
) -> SubmissionResult:
    return SubmissionResult(
        command_name=result.command_name,
        record_id=result.record_id,
        thread_id=result.thread_id,
        parent_id=result.parent_id,
        stored_path=result.stored_path,
        commit_id=result.commit_id,
        dry_run=result.dry_run,
        signature_path=result.signature_path,
        public_key_path=result.public_key_path,
        signer_fingerprint=result.signer_fingerprint,
        identity_id=result.identity_id,
        identity_bootstrap_path=result.identity_bootstrap_path,
        identity_bootstrap_created=result.identity_bootstrap_created,
        auto_reply_status=status,
        auto_reply_record_id=record_id,
        auto_reply_message=message,
        auto_reply_model=model,
    )
