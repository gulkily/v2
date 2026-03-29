from __future__ import annotations


def render_body(fields: list[tuple[str, str]]) -> str:
    return "\n".join(f"{key}: {value}" for key, value in fields) + "\n"


def render_error_body(error_code: str, message: str) -> str:
    return render_body(
        [
            ("Error-Code", error_code),
            ("Message", message),
        ]
    )


def render_preview_body(
    *,
    command_name: str,
    record_id: str,
    thread_id: str,
    stored_path: str,
    commit_message: str,
    parent_id: str | None = None,
    signature_path: str | None = None,
    public_key_path: str | None = None,
    signer_fingerprint: str | None = None,
    identity_id: str | None = None,
    identity_bootstrap_path: str | None = None,
    identity_bootstrap_created: bool | None = None,
    auto_reply_status: str | None = None,
    auto_reply_record_id: str | None = None,
    auto_reply_message: str | None = None,
    auto_reply_model: str | None = None,
) -> str:
    fields = [
        ("Command", command_name),
        ("Mode", "dry_run"),
        ("Record-ID", record_id),
        ("Thread-ID", thread_id),
    ]
    if parent_id:
        fields.append(("Parent-ID", parent_id))
    fields.extend(
        [
            ("Stored-Path", stored_path),
            ("Commit-Message", commit_message),
        ]
    )
    if signature_path:
        fields.append(("Signature-Path", signature_path))
    if public_key_path:
        fields.append(("Public-Key-Path", public_key_path))
    if signer_fingerprint:
        fields.append(("Signer-Fingerprint", signer_fingerprint))
    if identity_id:
        fields.append(("Identity-ID", identity_id))
    if identity_bootstrap_path:
        fields.append(("Identity-Bootstrap-Path", identity_bootstrap_path))
    if identity_bootstrap_created is not None:
        fields.append(("Identity-Bootstrap-Created", "yes" if identity_bootstrap_created else "no"))
    if auto_reply_status:
        fields.append(("Auto-Reply-Status", auto_reply_status))
    if auto_reply_record_id:
        fields.append(("Auto-Reply-Record-ID", auto_reply_record_id))
    if auto_reply_message:
        fields.append(("Auto-Reply-Message", auto_reply_message))
    if auto_reply_model:
        fields.append(("Auto-Reply-Model", auto_reply_model))
    return render_body(fields)


def render_success_body(
    *,
    record_id: str,
    thread_id: str,
    commit_id: str,
    stored_path: str,
    parent_id: str | None = None,
    signature_path: str | None = None,
    public_key_path: str | None = None,
    signer_fingerprint: str | None = None,
    identity_id: str | None = None,
    identity_bootstrap_path: str | None = None,
    identity_bootstrap_created: bool | None = None,
    auto_reply_status: str | None = None,
    auto_reply_record_id: str | None = None,
    auto_reply_message: str | None = None,
    auto_reply_model: str | None = None,
) -> str:
    fields = [
        ("Record-ID", record_id),
        ("Thread-ID", thread_id),
    ]
    if parent_id:
        fields.append(("Parent-ID", parent_id))
    fields.extend(
        [
            ("Commit-ID", commit_id),
            ("Stored-Path", stored_path),
        ]
    )
    if signature_path:
        fields.append(("Signature-Path", signature_path))
    if public_key_path:
        fields.append(("Public-Key-Path", public_key_path))
    if signer_fingerprint:
        fields.append(("Signer-Fingerprint", signer_fingerprint))
    if identity_id:
        fields.append(("Identity-ID", identity_id))
    if identity_bootstrap_path:
        fields.append(("Identity-Bootstrap-Path", identity_bootstrap_path))
    if identity_bootstrap_created is not None:
        fields.append(("Identity-Bootstrap-Created", "yes" if identity_bootstrap_created else "no"))
    if auto_reply_status:
        fields.append(("Auto-Reply-Status", auto_reply_status))
    if auto_reply_record_id:
        fields.append(("Auto-Reply-Record-ID", auto_reply_record_id))
    if auto_reply_message:
        fields.append(("Auto-Reply-Message", auto_reply_message))
    if auto_reply_model:
        fields.append(("Auto-Reply-Model", auto_reply_model))
    return render_body(fields)


def render_cgi_response(status: str, body: str) -> str:
    return (
        f"Status: {status}\n"
        "Content-Type: text/plain; charset=us-ascii\n"
        "\n"
        f"{body}"
    )


def render_submission_result(result) -> str:
    if result.dry_run:
        return render_preview_body(
            command_name=result.command_name,
            record_id=result.record_id,
            thread_id=result.thread_id,
            parent_id=result.parent_id,
            stored_path=result.stored_path,
            commit_message=f"{result.command_name}: {result.record_id}",
            signature_path=result.signature_path,
            public_key_path=result.public_key_path,
            signer_fingerprint=result.signer_fingerprint,
            identity_id=result.identity_id,
            identity_bootstrap_path=result.identity_bootstrap_path,
            identity_bootstrap_created=result.identity_bootstrap_created,
            auto_reply_status=result.auto_reply_status,
            auto_reply_record_id=result.auto_reply_record_id,
            auto_reply_message=result.auto_reply_message,
            auto_reply_model=result.auto_reply_model,
        )

    return render_success_body(
        record_id=result.record_id,
        thread_id=result.thread_id,
        parent_id=result.parent_id,
        commit_id=result.commit_id or "",
        stored_path=result.stored_path,
        signature_path=result.signature_path,
        public_key_path=result.public_key_path,
        signer_fingerprint=result.signer_fingerprint,
        identity_id=result.identity_id,
        identity_bootstrap_path=result.identity_bootstrap_path,
        identity_bootstrap_created=result.identity_bootstrap_created,
        auto_reply_status=result.auto_reply_status,
        auto_reply_record_id=result.auto_reply_record_id,
        auto_reply_message=result.auto_reply_message,
        auto_reply_model=result.auto_reply_model,
    )


def render_moderation_preview_body(
    *,
    command_name: str,
    record_id: str,
    action: str,
    target_type: str,
    target_id: str,
    timestamp: str,
    stored_path: str,
    commit_message: str,
    signature_path: str | None = None,
    public_key_path: str | None = None,
    signer_fingerprint: str | None = None,
    identity_id: str | None = None,
) -> str:
    fields = [
        ("Command", command_name),
        ("Mode", "dry_run"),
        ("Record-ID", record_id),
        ("Action", action),
        ("Target-Type", target_type),
        ("Target-ID", target_id),
        ("Timestamp", timestamp),
        ("Stored-Path", stored_path),
        ("Commit-Message", commit_message),
    ]
    if signature_path:
        fields.append(("Signature-Path", signature_path))
    if public_key_path:
        fields.append(("Public-Key-Path", public_key_path))
    if signer_fingerprint:
        fields.append(("Signer-Fingerprint", signer_fingerprint))
    if identity_id:
        fields.append(("Identity-ID", identity_id))
    return render_body(fields)


def render_moderation_success_body(
    *,
    record_id: str,
    action: str,
    target_type: str,
    target_id: str,
    timestamp: str,
    commit_id: str,
    stored_path: str,
    signature_path: str | None = None,
    public_key_path: str | None = None,
    signer_fingerprint: str | None = None,
    identity_id: str | None = None,
) -> str:
    fields = [
        ("Record-ID", record_id),
        ("Action", action),
        ("Target-Type", target_type),
        ("Target-ID", target_id),
        ("Timestamp", timestamp),
        ("Commit-ID", commit_id),
        ("Stored-Path", stored_path),
    ]
    if signature_path:
        fields.append(("Signature-Path", signature_path))
    if public_key_path:
        fields.append(("Public-Key-Path", public_key_path))
    if signer_fingerprint:
        fields.append(("Signer-Fingerprint", signer_fingerprint))
    if identity_id:
        fields.append(("Identity-ID", identity_id))
    return render_body(fields)


def render_moderation_result(result) -> str:
    if result.dry_run:
        return render_moderation_preview_body(
            command_name=result.command_name,
            record_id=result.record_id,
            action=result.action,
            target_type=result.target_type,
            target_id=result.target_id,
            timestamp=result.timestamp,
            stored_path=result.stored_path,
            commit_message=f"{result.command_name}: {result.record_id}",
            signature_path=result.signature_path,
            public_key_path=result.public_key_path,
            signer_fingerprint=result.signer_fingerprint,
            identity_id=result.identity_id,
        )

    return render_moderation_success_body(
        record_id=result.record_id,
        action=result.action,
        target_type=result.target_type,
        target_id=result.target_id,
        timestamp=result.timestamp,
        commit_id=result.commit_id or "",
        stored_path=result.stored_path,
        signature_path=result.signature_path,
        public_key_path=result.public_key_path,
        signer_fingerprint=result.signer_fingerprint,
        identity_id=result.identity_id,
    )


def render_merge_request_preview_body(
    *,
    command_name: str,
    record_id: str,
    action: str,
    requester_identity_id: str,
    target_identity_id: str,
    actor_identity_id: str,
    timestamp: str,
    stored_path: str,
    commit_message: str,
    signature_path: str | None = None,
    public_key_path: str | None = None,
    signer_fingerprint: str | None = None,
    identity_id: str | None = None,
) -> str:
    fields = [
        ("Command", command_name),
        ("Mode", "dry_run"),
        ("Record-ID", record_id),
        ("Action", action),
        ("Requester-Identity-ID", requester_identity_id),
        ("Target-Identity-ID", target_identity_id),
        ("Actor-Identity-ID", actor_identity_id),
        ("Timestamp", timestamp),
        ("Stored-Path", stored_path),
        ("Commit-Message", commit_message),
    ]
    if signature_path:
        fields.append(("Signature-Path", signature_path))
    if public_key_path:
        fields.append(("Public-Key-Path", public_key_path))
    if signer_fingerprint:
        fields.append(("Signer-Fingerprint", signer_fingerprint))
    if identity_id:
        fields.append(("Identity-ID", identity_id))
    return render_body(fields)


def render_merge_request_success_body(
    *,
    record_id: str,
    action: str,
    requester_identity_id: str,
    target_identity_id: str,
    actor_identity_id: str,
    timestamp: str,
    commit_id: str,
    stored_path: str,
    signature_path: str | None = None,
    public_key_path: str | None = None,
    signer_fingerprint: str | None = None,
    identity_id: str | None = None,
) -> str:
    fields = [
        ("Record-ID", record_id),
        ("Action", action),
        ("Requester-Identity-ID", requester_identity_id),
        ("Target-Identity-ID", target_identity_id),
        ("Actor-Identity-ID", actor_identity_id),
        ("Timestamp", timestamp),
        ("Commit-ID", commit_id),
        ("Stored-Path", stored_path),
    ]
    if signature_path:
        fields.append(("Signature-Path", signature_path))
    if public_key_path:
        fields.append(("Public-Key-Path", public_key_path))
    if signer_fingerprint:
        fields.append(("Signer-Fingerprint", signer_fingerprint))
    if identity_id:
        fields.append(("Identity-ID", identity_id))
    return render_body(fields)


def render_merge_request_result(result) -> str:
    if result.dry_run:
        return render_merge_request_preview_body(
            command_name=result.command_name,
            record_id=result.record_id,
            action=result.action,
            requester_identity_id=result.requester_identity_id,
            target_identity_id=result.target_identity_id,
            actor_identity_id=result.actor_identity_id,
            timestamp=result.timestamp,
            stored_path=result.stored_path,
            commit_message=f"{result.command_name}: {result.record_id}",
            signature_path=result.signature_path,
            public_key_path=result.public_key_path,
            signer_fingerprint=result.signer_fingerprint,
            identity_id=result.identity_id,
        )

    return render_merge_request_success_body(
        record_id=result.record_id,
        action=result.action,
        requester_identity_id=result.requester_identity_id,
        target_identity_id=result.target_identity_id,
        actor_identity_id=result.actor_identity_id,
        timestamp=result.timestamp,
        commit_id=result.commit_id or "",
        stored_path=result.stored_path,
        signature_path=result.signature_path,
        public_key_path=result.public_key_path,
        signer_fingerprint=result.signer_fingerprint,
        identity_id=result.identity_id,
    )


def render_identity_link_preview_body(
    *,
    command_name: str,
    record_id: str,
    action: str,
    source_identity_id: str,
    target_identity_id: str,
    timestamp: str,
    stored_path: str,
    commit_message: str,
    signature_path: str | None = None,
    public_key_path: str | None = None,
    signer_fingerprint: str | None = None,
    identity_id: str | None = None,
) -> str:
    fields = [
        ("Command", command_name),
        ("Mode", "dry_run"),
        ("Record-ID", record_id),
        ("Action", action),
        ("Source-Identity-ID", source_identity_id),
        ("Target-Identity-ID", target_identity_id),
        ("Timestamp", timestamp),
        ("Stored-Path", stored_path),
        ("Commit-Message", commit_message),
    ]
    if signature_path:
        fields.append(("Signature-Path", signature_path))
    if public_key_path:
        fields.append(("Public-Key-Path", public_key_path))
    if signer_fingerprint:
        fields.append(("Signer-Fingerprint", signer_fingerprint))
    if identity_id:
        fields.append(("Identity-ID", identity_id))
    return render_body(fields)


def render_identity_link_success_body(
    *,
    record_id: str,
    action: str,
    source_identity_id: str,
    target_identity_id: str,
    timestamp: str,
    commit_id: str,
    stored_path: str,
    signature_path: str | None = None,
    public_key_path: str | None = None,
    signer_fingerprint: str | None = None,
    identity_id: str | None = None,
) -> str:
    fields = [
        ("Record-ID", record_id),
        ("Action", action),
        ("Source-Identity-ID", source_identity_id),
        ("Target-Identity-ID", target_identity_id),
        ("Timestamp", timestamp),
        ("Commit-ID", commit_id),
        ("Stored-Path", stored_path),
    ]
    if signature_path:
        fields.append(("Signature-Path", signature_path))
    if public_key_path:
        fields.append(("Public-Key-Path", public_key_path))
    if signer_fingerprint:
        fields.append(("Signer-Fingerprint", signer_fingerprint))
    if identity_id:
        fields.append(("Identity-ID", identity_id))
    return render_body(fields)


def render_identity_link_result(result) -> str:
    if result.dry_run:
        return render_identity_link_preview_body(
            command_name=result.command_name,
            record_id=result.record_id,
            action=result.action,
            source_identity_id=result.source_identity_id,
            target_identity_id=result.target_identity_id,
            timestamp=result.timestamp,
            stored_path=result.stored_path,
            commit_message=f"{result.command_name}: {result.record_id}",
            signature_path=result.signature_path,
            public_key_path=result.public_key_path,
            signer_fingerprint=result.signer_fingerprint,
            identity_id=result.identity_id,
        )

    return render_identity_link_success_body(
        record_id=result.record_id,
        action=result.action,
        source_identity_id=result.source_identity_id,
        target_identity_id=result.target_identity_id,
        timestamp=result.timestamp,
        commit_id=result.commit_id or "",
        stored_path=result.stored_path,
        signature_path=result.signature_path,
        public_key_path=result.public_key_path,
        signer_fingerprint=result.signer_fingerprint,
        identity_id=result.identity_id,
    )


def render_profile_update_preview_body(
    *,
    command_name: str,
    record_id: str,
    action: str,
    source_identity_id: str,
    timestamp: str,
    display_name: str,
    stored_path: str,
    commit_message: str,
    signature_path: str | None = None,
    public_key_path: str | None = None,
    signer_fingerprint: str | None = None,
    identity_id: str | None = None,
) -> str:
    fields = [
        ("Command", command_name),
        ("Mode", "dry_run"),
        ("Record-ID", record_id),
        ("Action", action),
        ("Source-Identity-ID", source_identity_id),
        ("Timestamp", timestamp),
        ("Display-Name", display_name),
        ("Stored-Path", stored_path),
        ("Commit-Message", commit_message),
    ]
    if signature_path:
        fields.append(("Signature-Path", signature_path))
    if public_key_path:
        fields.append(("Public-Key-Path", public_key_path))
    if signer_fingerprint:
        fields.append(("Signer-Fingerprint", signer_fingerprint))
    if identity_id:
        fields.append(("Identity-ID", identity_id))
    return render_body(fields)


def render_profile_update_success_body(
    *,
    record_id: str,
    action: str,
    source_identity_id: str,
    timestamp: str,
    display_name: str,
    commit_id: str,
    stored_path: str,
    signature_path: str | None = None,
    public_key_path: str | None = None,
    signer_fingerprint: str | None = None,
    identity_id: str | None = None,
) -> str:
    fields = [
        ("Record-ID", record_id),
        ("Action", action),
        ("Source-Identity-ID", source_identity_id),
        ("Timestamp", timestamp),
        ("Display-Name", display_name),
        ("Commit-ID", commit_id),
        ("Stored-Path", stored_path),
    ]
    if signature_path:
        fields.append(("Signature-Path", signature_path))
    if public_key_path:
        fields.append(("Public-Key-Path", public_key_path))
    if signer_fingerprint:
        fields.append(("Signer-Fingerprint", signer_fingerprint))
    if identity_id:
        fields.append(("Identity-ID", identity_id))
    return render_body(fields)


def render_profile_update_result(result) -> str:
    if result.dry_run:
        return render_profile_update_preview_body(
            command_name=result.command_name,
            record_id=result.record_id,
            action=result.action,
            source_identity_id=result.source_identity_id,
            timestamp=result.timestamp,
            display_name=result.display_name,
            stored_path=result.stored_path,
            commit_message=f"{result.command_name}: {result.record_id}",
            signature_path=result.signature_path,
            public_key_path=result.public_key_path,
            signer_fingerprint=result.signer_fingerprint,
            identity_id=result.identity_id,
        )

    return render_profile_update_success_body(
        record_id=result.record_id,
        action=result.action,
        source_identity_id=result.source_identity_id,
        timestamp=result.timestamp,
        display_name=result.display_name,
        commit_id=result.commit_id or "",
        stored_path=result.stored_path,
        signature_path=result.signature_path,
        public_key_path=result.public_key_path,
        signer_fingerprint=result.signer_fingerprint,
        identity_id=result.identity_id,
    )


def render_thread_title_update_preview_body(
    *,
    command_name: str,
    record_id: str,
    thread_id: str,
    timestamp: str,
    title: str,
    stored_path: str,
    commit_message: str,
    signature_path: str | None = None,
    public_key_path: str | None = None,
    signer_fingerprint: str | None = None,
    identity_id: str | None = None,
) -> str:
    fields = [
        ("Command", command_name),
        ("Mode", "dry_run"),
        ("Record-ID", record_id),
        ("Thread-ID", thread_id),
        ("Timestamp", timestamp),
        ("Title", title),
        ("Stored-Path", stored_path),
        ("Commit-Message", commit_message),
    ]
    if signature_path:
        fields.append(("Signature-Path", signature_path))
    if public_key_path:
        fields.append(("Public-Key-Path", public_key_path))
    if signer_fingerprint:
        fields.append(("Signer-Fingerprint", signer_fingerprint))
    if identity_id:
        fields.append(("Identity-ID", identity_id))
    return render_body(fields)


def render_thread_title_update_success_body(
    *,
    record_id: str,
    thread_id: str,
    timestamp: str,
    title: str,
    commit_id: str,
    stored_path: str,
    signature_path: str | None = None,
    public_key_path: str | None = None,
    signer_fingerprint: str | None = None,
    identity_id: str | None = None,
) -> str:
    fields = [
        ("Record-ID", record_id),
        ("Thread-ID", thread_id),
        ("Timestamp", timestamp),
        ("Title", title),
        ("Commit-ID", commit_id),
        ("Stored-Path", stored_path),
    ]
    if signature_path:
        fields.append(("Signature-Path", signature_path))
    if public_key_path:
        fields.append(("Public-Key-Path", public_key_path))
    if signer_fingerprint:
        fields.append(("Signer-Fingerprint", signer_fingerprint))
    if identity_id:
        fields.append(("Identity-ID", identity_id))
    return render_body(fields)


def render_thread_title_update_result(result) -> str:
    if result.dry_run:
        return render_thread_title_update_preview_body(
            command_name=result.command_name,
            record_id=result.record_id,
            thread_id=result.thread_id,
            timestamp=result.timestamp,
            title=result.title,
            stored_path=result.stored_path,
            commit_message=f"{result.command_name}: {result.record_id}",
            signature_path=result.signature_path,
            public_key_path=result.public_key_path,
            signer_fingerprint=result.signer_fingerprint,
            identity_id=result.identity_id,
        )

    return render_thread_title_update_success_body(
        record_id=result.record_id,
        thread_id=result.thread_id,
        timestamp=result.timestamp,
        title=result.title,
        commit_id=result.commit_id or "",
        stored_path=result.stored_path,
        signature_path=result.signature_path,
        public_key_path=result.public_key_path,
        signer_fingerprint=result.signer_fingerprint,
        identity_id=result.identity_id,
    )
