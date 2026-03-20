#!/usr/bin/env python3
"""Diagnose and repair common git checkout issues for operator-managed repos."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RepoDiagnosis:
    is_healthy: bool
    summary: str
    details: tuple[str, ...] = ()


def run_git_recover(repo_root: Path, *, apply: bool = False) -> int:
    diagnosis = diagnose_repo(repo_root)
    print(diagnosis.summary)
    for line in diagnosis.details:
        print(line)

    if diagnosis.is_healthy:
        return 0

    if not apply:
        print("Re-run with `./forum git-recover --apply` to attempt an automatic repair.")
        return 1

    print("Automatic repair is not implemented yet for this git state.")
    return 1


def diagnose_repo(repo_root: Path) -> RepoDiagnosis:
    branch_result = git(repo_root, "branch", "--show-current")
    status_result = git(repo_root, "status", "--short", "--branch")

    if branch_result.returncode != 0 or status_result.returncode != 0:
        return RepoDiagnosis(
            is_healthy=False,
            summary="Git recovery could not inspect the repository state.",
            details=_error_lines(branch_result, status_result),
        )

    branch = branch_result.stdout.strip()
    status_lines = [line.rstrip() for line in status_result.stdout.splitlines() if line.strip()]
    if not status_lines:
        return RepoDiagnosis(
            is_healthy=False,
            summary="Git recovery could not determine repository status output.",
        )

    branch_header = status_lines[0]
    working_tree_clean = len(status_lines) == 1
    if branch == "main" and branch_header == "## main...origin/main" and working_tree_clean:
        return RepoDiagnosis(
            is_healthy=True,
            summary="Git checkout is healthy: on `main`, tracking `origin/main`, and clean.",
        )

    details = (
        f"Current branch: {branch or '(detached or unknown)'}",
        f"Status: {branch_header}",
        "Working tree is clean." if working_tree_clean else "Working tree has local changes.",
    )
    return RepoDiagnosis(
        is_healthy=False,
        summary="Git checkout needs recovery review.",
        details=details,
    )


def git(repo_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        check=False,
        cwd=repo_root,
        text=True,
        capture_output=True,
    )


def _error_lines(*results: subprocess.CompletedProcess[str]) -> tuple[str, ...]:
    lines: list[str] = []
    for result in results:
        stderr = (result.stderr or "").strip()
        if stderr:
            lines.append(stderr)
    return tuple(lines)
