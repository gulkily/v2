#!/usr/bin/env python3
"""Operator-facing helpers for archival and history purge workflows."""

from __future__ import annotations

import subprocess
import sys
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
import zipfile

SUGGESTED_PURGE_ORDER = (
    "records/posts",
    "records/identity",
    "records/identity-links",
    "records/merge-requests",
    "records/profile-updates",
    "records/moderation",
    "records/public-keys",
)
PRESERVED_RECORDS_PATHS = {
    "records/instance",
    "records/system",
}


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
    used_default_paths: bool = False


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
    if plan.used_default_paths:
        print("No explicit paths were provided. Using suggested default paths from the current records tree.")
    print("Selected paths:")
    for path in plan.requested_paths:
        print(f"- {path}")

    if not dry_run:
        dirty_worktree = worktree_is_dirty(repo_root)
        if dirty_worktree and not force:
            print(
                "Refusing to apply content purge on a dirty worktree. Clean the checkout or re-run with `--force`.",
                file=sys.stderr,
            )
            return 1
        if dirty_worktree and force:
            print("Force flag enabled: continuing despite dirty worktree.")
        try:
            ensure_filter_repo_available(repo_root)
            create_normalized_archive(plan, repo_root)
            write_archive_manifest(plan, repo_root)
            rewrite_history(repo_root, plan)
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 1

        print(f"Archive created: {plan.archive_output}")
        print(f"Manifest created: {plan.manifest_output}")
        print("History rewrite completed for the selected paths.")
        print("Required follow-up actions:")
        for line in render_post_rewrite_instructions():
            print(f"- {line}")
        return 0

    print("Preview only: no archive was created and no history was rewritten.")
    return 0


def build_purge_plan(
    repo_root: Path,
    *,
    requested_paths: list[str],
    archive_output: Path | None = None,
) -> PurgePlan:
    explicit_paths = bool(requested_paths)
    normalized_paths = (
        tuple(normalize_requested_path(path) for path in requested_paths)
        if explicit_paths
        else suggest_default_purge_paths(repo_root)
    )
    selected_paths = resolve_purge_paths(repo_root, list(normalized_paths))
    archived_files = collect_archived_files(selected_paths)
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    archive_path = resolve_archive_output_path(
        repo_root,
        archive_output=archive_output,
        requested_paths=list(normalized_paths),
        generated_at=generated_at,
    )
    manifest_path = archive_path.with_suffix(".manifest.txt")
    head_commit = git_stdout(repo_root, "rev-parse", "HEAD")
    oldest_reachable_commit = git_stdout(repo_root, "rev-list", "--max-parents=0", "HEAD").splitlines()[0]
    return PurgePlan(
        requested_paths=normalized_paths,
        selected_paths=selected_paths,
        archived_files=archived_files,
        archive_output=archive_path,
        manifest_output=manifest_path,
        generated_at=generated_at,
        head_commit=head_commit,
        oldest_reachable_commit=oldest_reachable_commit,
        used_default_paths=not explicit_paths,
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


def suggest_default_purge_paths(repo_root: Path) -> tuple[str, ...]:
    records_root = repo_root / "records"
    if not records_root.exists():
        raise ValueError("Repository does not contain a `records/` tree to inspect for purge suggestions.")

    suggestions: list[str] = []
    known = set()
    for path_text in SUGGESTED_PURGE_ORDER:
        candidate = repo_root / path_text
        if candidate.exists() and directory_contains_purgeable_files(candidate):
            suggestions.append(path_text)
            known.add(path_text)

    for child in sorted(records_root.iterdir(), key=lambda path: path.name):
        normalized = f"records/{child.name}"
        if normalized in known or normalized in PRESERVED_RECORDS_PATHS:
            continue
        if child.is_dir() and directory_contains_purgeable_files(child):
            suggestions.append(normalized)
        elif child.is_file() and child.name != "README.md":
            suggestions.append(normalized)

    if not suggestions:
        raise ValueError(
            "No explicit paths were provided and no suggested purge paths were found under `records/`. "
            "Pass one or more canonical `records/` paths explicitly."
        )
    return tuple(suggestions)


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


def directory_contains_purgeable_files(directory: Path) -> bool:
    for path in directory.rglob("*"):
        if path.is_file() and path.name != "README.md":
            return True
    return False


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


def create_normalized_archive(plan: PurgePlan, repo_root: Path) -> None:
    plan.archive_output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(plan.archive_output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for source_path in plan.archived_files:
            archive_name = source_path.relative_to(repo_root).as_posix()
            archive_info = zipfile.ZipInfo(filename=archive_name, date_time=(2020, 1, 1, 0, 0, 0))
            archive_info.compress_type = zipfile.ZIP_DEFLATED
            archive_info.external_attr = 0o100644 << 16
            archive.writestr(archive_info, source_path.read_bytes())


def write_archive_manifest(plan: PurgePlan, repo_root: Path) -> None:
    plan.manifest_output.parent.mkdir(parents=True, exist_ok=True)
    plan.manifest_output.write_text(build_archive_manifest(plan, repo_root), encoding="utf-8")


def ensure_filter_repo_available(repo_root: Path) -> None:
    del repo_root
    executable = shutil.which("git-filter-repo")
    if executable is None:
        raise ValueError(
            "Cannot apply content purge because `git filter-repo` is not available in this environment. "
            "Install the `git-filter-repo` executable before running `content-purge --apply`."
        )


def rewrite_history(repo_root: Path, plan: PurgePlan) -> None:
    command = ["git", "-C", str(repo_root), "filter-repo", "--force"]
    for path in plan.requested_paths:
        command.extend(["--path", path])
    command.append("--invert-paths")
    result = subprocess.run(
        command,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "git filter-repo failed"
        raise ValueError(f"History rewrite failed: {detail}")


def render_post_rewrite_instructions() -> tuple[str, ...]:
    return (
        "Force-push rewritten branches to the canonical remote, for example `git push --force --all origin`.",
        "Force-push rewritten tags if this repository publishes tags, for example `git push --force --tags origin`.",
        "Retire or reclone old checkouts so future operators start from the rewritten history.",
        "Remove or refresh any remote mirrors, caches, or backups that still contain the purged content.",
    )


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
