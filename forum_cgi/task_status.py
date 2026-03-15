from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from forum_cgi.posting import PostingError, build_commit_message, commit_post, records_dir, write_ascii_file
from forum_web.repository import is_task_root, parse_post


@dataclass(frozen=True)
class TaskStatusUpdateResult:
    task_id: str
    previous_status: str
    status: str
    stored_path: str
    commit_id: str


def resolve_task_root_path(repo_root: Path, task_id: str) -> Path:
    return records_dir(repo_root) / f"{task_id}.txt"


def replace_header_value(raw_text: str, *, header_name: str, new_value: str) -> str:
    header_text, separator, body_text = raw_text.partition("\n\n")
    if not separator:
        raise PostingError("bad_request", "task root is missing header/body separator")

    prefix = f"{header_name}: "
    updated_lines: list[str] = []
    replaced = False
    for line in header_text.splitlines():
        if line.startswith(prefix):
            updated_lines.append(f"{header_name}: {new_value}")
            replaced = True
            continue
        updated_lines.append(line)

    if not replaced:
        raise PostingError("bad_request", f"task root is missing required header: {header_name}")

    return "\n".join(updated_lines) + "\n\n" + body_text


def submit_mark_task_done(task_id: str, repo_root: Path) -> TaskStatusUpdateResult:
    task_path = resolve_task_root_path(repo_root, task_id)
    if not task_path.exists():
        raise LookupError(f"unknown task: {task_id}")

    task_post = parse_post(task_path)
    if not is_task_root(task_post) or task_post.task_metadata is None:
        raise LookupError(f"unknown task: {task_id}")

    previous_status = task_post.task_metadata.status
    if previous_status.strip().lower() == "done":
        raise PostingError("conflict", f"task is already done: {task_id}", status="409 Conflict")

    updated_text = replace_header_value(
        task_path.read_text(encoding="ascii"),
        header_name="Task-Status",
        new_value="done",
    )
    write_ascii_file(task_path, updated_text)
    commit_id = commit_post(
        repo_root,
        [task_path],
        message=build_commit_message("mark_task_done", task_id),
    )
    return TaskStatusUpdateResult(
        task_id=task_id,
        previous_status=previous_status,
        status="done",
        stored_path=str(task_path.relative_to(repo_root)),
        commit_id=commit_id,
    )
