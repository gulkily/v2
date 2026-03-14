from __future__ import annotations

import subprocess
import sys

from forum_cgi.posting import (
    PostingError,
    build_preview,
    get_repo_root,
    parse_payload,
    read_ascii_payload,
    store_post,
    validate_create_reply,
    validate_create_thread,
)
from forum_cgi.text import (
    render_cgi_response,
    render_error_body,
    render_preview_body,
    render_success_body,
)


def run_create_thread() -> int:
    try:
        payload_text = read_ascii_payload()
        post = parse_payload(payload_text)
        repo_root = get_repo_root()
        validate_create_thread(post)
        commit_id, stored_path = store_post("create_thread", post, repo_root, payload_text)
        response = render_cgi_response(
            "200 OK",
            render_success_body(
                record_id=post.post_id,
                thread_id=post.post_id,
                commit_id=commit_id,
                stored_path=stored_path,
            ),
        )
    except PostingError as exc:
        response = render_cgi_response(exc.status, render_error_body(exc.error_code, exc.message))
    except subprocess.CalledProcessError as exc:
        response = render_cgi_response(
            "500 Internal Server Error",
            render_error_body("internal_error", f"git command failed: {exc.cmd[0]}"),
        )
    print(response, end="")
    return 0


def run_create_reply() -> int:
    try:
        payload_text = read_ascii_payload()
        post = parse_payload(payload_text)
        repo_root = get_repo_root()
        validate_create_reply(post, repo_root)
        preview = build_preview("create_reply", post, repo_root)
        response = render_cgi_response(
            "200 OK",
            render_preview_body(
                command_name=preview.command_name,
                record_id=preview.record_id,
                thread_id=preview.thread_id,
                parent_id=preview.parent_id,
                stored_path=preview.stored_path,
                commit_message=preview.commit_message,
            ),
        )
    except PostingError as exc:
        response = render_cgi_response(exc.status, render_error_body(exc.error_code, exc.message))
    except subprocess.CalledProcessError as exc:
        response = render_cgi_response(
            "500 Internal Server Error",
            render_error_body("internal_error", f"git command failed: {exc.cmd[0]}"),
        )
    print(response, end="")
    return 0


def main(command_name: str) -> int:
    if command_name == "create_thread":
        return run_create_thread()
    if command_name == "create_reply":
        return run_create_reply()

    print(
        render_cgi_response(
            "400 Bad Request",
            render_error_body("bad_request", f"unknown command: {command_name}"),
        ),
        end="",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else ""))
