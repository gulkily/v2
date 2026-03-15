from __future__ import annotations

import subprocess
import sys

from forum_cgi.posting import PostingError, get_repo_root, read_ascii_payload
from forum_cgi.service import submit_create_reply, submit_create_thread
from forum_cgi.text import (
    render_cgi_response,
    render_error_body,
    render_submission_result,
)


def run_create_thread() -> int:
    try:
        payload_text = read_ascii_payload()
        repo_root = get_repo_root()
        result = submit_create_thread(payload_text, repo_root, dry_run=False)
        response = render_cgi_response("200 OK", render_submission_result(result))
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
        repo_root = get_repo_root()
        result = submit_create_reply(payload_text, repo_root, dry_run=False)
        response = render_cgi_response("200 OK", render_submission_result(result))
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
