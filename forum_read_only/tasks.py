from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class TaskRecord:
    task_id: str
    title: str
    status: str
    presentability_impact: float
    implementation_difficulty: float
    dependencies: tuple[str, ...]
    sources: tuple[str, ...]
    summary: str
    path: Path
    discussion_thread_id: str | None = None


def task_records_dir(repo_root: Path) -> Path:
    return repo_root / "records" / "tasks"


def parse_task_text(raw_text: str, *, source_path: Path | None = None) -> TaskRecord:
    header_text, separator, body_text = raw_text.partition("\n\n")
    if not separator:
        raise ValueError("task text is missing header/body separator")

    headers: dict[str, str] = {}
    for line in header_text.splitlines():
        if ": " not in line:
            raise ValueError(f"invalid header line: {line!r}")
        key, value = line.split(": ", 1)
        headers[key] = value.strip()

    task_id = require_header(headers, "Task-ID")
    title = require_header(headers, "Title")
    status = require_header(headers, "Status")
    sources = split_semicolon_header(require_header(headers, "Sources"))
    if not sources:
        raise ValueError("Sources must include at least one source reference")

    summary = body_text.rstrip("\n")
    if not summary.strip():
        raise ValueError("task text is missing summary body")

    return TaskRecord(
        task_id=task_id,
        title=title,
        status=status,
        presentability_impact=parse_rating_header(headers, "Presentability-Impact"),
        implementation_difficulty=parse_rating_header(headers, "Implementation-Difficulty"),
        dependencies=split_space_header(headers.get("Depends-On", "")),
        sources=sources,
        summary=summary,
        path=source_path or Path("<request>"),
        discussion_thread_id=headers.get("Discussion-Thread-ID") or None,
    )


def require_header(headers: dict[str, str], header_name: str) -> str:
    value = headers.get(header_name, "").strip()
    if not value:
        raise ValueError(f"task text is missing required header: {header_name}")
    return value


def parse_rating_header(headers: dict[str, str], header_name: str) -> float:
    raw_value = require_header(headers, header_name)
    try:
        value = float(raw_value)
    except ValueError as exc:
        raise ValueError(f"{header_name} must be a decimal rating") from exc
    if value < 0 or value > 1:
        raise ValueError(f"{header_name} must be between 0 and 1")
    return value


def split_space_header(raw_value: str) -> tuple[str, ...]:
    return tuple(part for part in raw_value.split() if part)


def split_semicolon_header(raw_value: str) -> tuple[str, ...]:
    return tuple(part.strip() for part in raw_value.split(";") if part.strip())


def parse_task(path: Path) -> TaskRecord:
    return parse_task_text(path.read_text(encoding="ascii"), source_path=path)


def load_tasks(records_dir: Path) -> list[TaskRecord]:
    if not records_dir.exists():
        return []
    tasks = [parse_task(path) for path in sorted(records_dir.glob("*.txt"))]
    validate_task_graph(tasks)
    return sorted(tasks, key=lambda task: task.task_id)


def index_tasks(tasks: list[TaskRecord]) -> dict[str, TaskRecord]:
    return {task.task_id: task for task in tasks}


def validate_task_graph(tasks: list[TaskRecord]) -> None:
    indexed = index_tasks(tasks)
    if len(indexed) != len(tasks):
        raise ValueError("task graph contains duplicate Task-ID values")

    for task in tasks:
        if len(set(task.dependencies)) != len(task.dependencies):
            raise ValueError(f"task {task.task_id} declares duplicate dependencies")
        for dependency in task.dependencies:
            if dependency == task.task_id:
                raise ValueError(f"task {task.task_id} cannot depend on itself")
            if dependency not in indexed:
                raise ValueError(f"task {task.task_id} depends on unknown task {dependency}")

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(task_id: str) -> None:
        if task_id in visited:
            return
        if task_id in visiting:
            raise ValueError(f"task dependency cycle detected at {task_id}")
        visiting.add(task_id)
        for dependency in indexed[task_id].dependencies:
            visit(dependency)
        visiting.remove(task_id)
        visited.add(task_id)

    for task in tasks:
        visit(task.task_id)
