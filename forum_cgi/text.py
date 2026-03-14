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
    return render_body(fields)


def render_success_body(
    *,
    record_id: str,
    thread_id: str,
    commit_id: str,
    stored_path: str,
    parent_id: str | None = None,
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
    return render_body(fields)


def render_cgi_response(status: str, body: str) -> str:
    return (
        f"Status: {status}\n"
        "Content-Type: text/plain; charset=us-ascii\n"
        "\n"
        f"{body}"
    )
