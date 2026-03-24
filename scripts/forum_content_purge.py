#!/usr/bin/env python3
"""Operator-facing helpers for archival and history purge workflows."""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

@dataclass(frozen=True)
class PurgePlan:
    requested_paths: tuple[str, ...]
    selected_paths: tuple[Path, ...]
    archived_files: tuple[Path, ...]
    archive_output: Path
    manifest_output: Path
    generated_at: str
    head_commit: str
    oldest_reachable_commit: str


def run_content_purge(
    repo_root: Path,
    *,
    paths: list[str],
    archive_output: Path | None = None,
    dry_run: bool = True,
    force: bool = False,
) -> int:
    try:
        plan = build_purge_plan(repo_root, requested_paths=paths, archive_output=archive_output)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print("Content purge workflow preview")
    print(f"Repository root: {repo_root}")
    print(f"Mode: {'preview' if dry_run else 'apply'}")
    print(f"Archive output: {plan.archive_output}")
    print(f"Manifest output: {plan.manifest_output}")
    print(f"Head commit: {plan.head_commit}")
    print(f"Oldest reachable commit: {plan.oldest_reachable_commit}")
    print(f"Selected path count: {len(plan.selected_paths)}")
    print(f"Archived file count: {len(plan.archived_files)}")
    print("Selected paths:")
    for path in plan.requested_paths:
        print(f"- {path}")

    if not dry_run:
        if worktree_is_dirty(repo_root) and not force:
            print(
                "Refusing to apply content purge on a dirty worktree. Clean the checkout or re-run with `--force`.",
                file=sys.stderr,
            )
            return 1
        if force:
            print("Force flag recorded: dirty-worktree guard may be bypassed in later stages.")
        print("Apply mode is not implemented yet. Re-run without `--apply` for preview output.")
        return 1

    print("Preview only: no archive was created and no history was rewritten.")
    return 0


def build_purge_plan(
    repo_root: Path,
    *,
    requested_paths: list[str],
    archive_output: Path | None = None,
) -> PurgePlan:
    selected_paths = resolve_purge_paths(repo_root, requested_paths)
    archived_files = collect_archived_files(selected_paths)
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    archive_path = resolve_archive_output_path(
        repo_root,
        archive_output=archive_output,
        requested_paths=requested_paths,
        generated_at=generated_at,
    )
    manifest_path = archive_path.with_suffix(".manifest.txt")
    head_commit = git_stdout(repo_root, "rev-parse", "HEAD")
    oldest_reachable_commit = git_stdout(repo_root, "rev-list", "--max-parents=0", "HEAD").splitlines()[0]
    return PurgePlan(
        requested_paths=tuple(normalize_requested_path(path) for path in requested_paths),
        selected_paths=selected_paths,
        archived_files=archived_files,
        archive_output=archive_path,
        manifest_output=manifest_path,
        generated_at=generated_at,
        head_commit=head_commit,
        oldest_reachable_commit=oldest_reachable_commit,
    )


def resolve_purge_paths(repo_root: Path, requested_paths: list[str]) -> tuple[Path, ...]:
    if not requested_paths:
        raise ValueError("At least one canonical `records/` path is required.")

    records_root = (repo_root / "records").resolve()
    normalized_paths: list[str] = []
    resolved_paths: list[Path] = []
    for raw_path in requested_paths:
        normalized = normalize_requested_path(raw_path)
        if normalized == "records":
            raise ValueError("Select one or more record families under `records/`, not the `records/` root itself.")
        if not normalized.startswith("records/"):
            raise ValueError(
                f"Path `{raw_path}` is outside the supported canonical content area. Select paths under `records/`."
            )
        candidate = (repo_root / normalized).resolve()
        if records_root not in candidate.parents and candidate != records_root:
            raise ValueError(f"Path `{raw_path}` does not resolve inside the repository `records/` tree.")
        if not candidate.exists():
            raise ValueError(f"Path `{raw_path}` does not exist in this checkout.")
        normalized_paths.append(normalized)
        resolved_paths.append(candidate)

    seen = set()
    for normalized in normalized_paths:
        if normalized in seen:
            raise ValueError(f"Duplicate purge path `{normalized}` was provided.")
        seen.add(normalized)

    sorted_pairs = sorted(zip(normalized_paths, resolved_paths), key=lambda pair: pair[0])
    for index, (left, _) in enumerate(sorted_pairs):
        for right, _ in sorted_pairs[index + 1 :]:
            if right.startswith(f"{left}/"):
                raise ValueError(
                    f"Overlapping purge paths are not allowed: `{left}` already covers nested selection `{right}`."
                )

    return tuple(path for _, path in sorted_pairs)


def normalize_requested_path(raw_path: str) -> str:
    stripped = raw_path.strip()
    if not stripped:
        raise ValueError("Empty purge paths are not allowed.")
    path = PurePosixPath(stripped)
    if path.is_absolute():
        raise ValueError(f"Absolute path `{raw_path}` is not allowed. Use repository-relative paths.")
    if any(part in ("", ".", "..") for part in path.parts):
        raise ValueError(f"Path `{raw_path}` must be a simple repository-relative path without `.` or `..`.")
    return path.as_posix().rstrip("/")


def collect_archived_files(selected_paths: tuple[Path, ...]) -> tuple[Path, ...]:
    archived: list[Path] = []
    for selected_path in selected_paths:
        if selected_path.is_file():
            archived.append(selected_path)
            continue
        archived.extend(sorted(path for path in selected_path.rglob("*") if path.is_file()))
    if not archived:
        raise ValueError("Selected purge paths do not contain any files to archive.")
    return tuple(sorted(archived))


def resolve_archive_output_path(
    repo_root: Path,
    *,
    archive_output: Path | None,
    requested_paths: list[str],
    generated_at: str,
) -> Path:
    if archive_output is not None:
        resolved = archive_output.expanduser()
        if not resolved.is_absolute():
            resolved = (repo_root / resolved).resolve()
        else:
            resolved = resolved.resolve()
    else:
        slug = "-".join(path.split("/", 1)[1].replace("/", "-") for path in requested_paths)
        timestamp = generated_at.replace(":", "").replace("-", "")
        resolved = (repo_root.parent / f"{repo_root.name}-{slug}-{timestamp}.zip").resolve()

    if repo_root.resolve() == resolved or repo_root.resolve() in resolved.parents:
        raise ValueError("Archive output must live outside the repository root.")
    return resolved


def build_archive_manifest(plan: PurgePlan, repo_root: Path) -> str:
    lines = [
        "CONTENT-PURGE-MANIFEST/1",
        f"Repository-Root: {repo_root}",
        f"Generated-At: {plan.generated_at}",
        f"Head-Commit: {plan.head_commit}",
        f"Oldest-Reachable-Commit: {plan.oldest_reachable_commit}",
        f"Archive-Output: {plan.archive_output}",
        f"Selected-Path-Count: {len(plan.requested_paths)}",
        f"Archived-File-Count: {len(plan.archived_files)}",
        "",
        "Selected-Paths:",
    ]
    lines.extend(f"- {path}" for path in plan.requested_paths)
    lines.append("")
    lines.append("Archived-Files:")
    lines.extend(f"- {path.relative_to(repo_root).as_posix()}" for path in plan.archived_files)
    lines.append("")
    return "\n".join(lines)


def worktree_is_dirty(repo_root: Path) -> bool:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "status", "--short"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return result.returncode != 0 or bool(result.stdout.strip())


def git_stdout(repo_root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "git command failed"
        raise ValueError(f"`git {' '.join(args)}` failed: {detail}")
    return result.stdout.strip()
