#!/usr/bin/env python3
"""Diagnose and repair common git checkout issues for operator-managed repos."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

TARGET_BRANCH = "main"
TARGET_UPSTREAM = "origin/main"
TARGET_PULL_FF = "only"

ISSUE_ORDER = {
    "rebase_in_progress": 10,
    "merge_in_progress": 20,
    "detached_head": 30,
    "missing_upstream": 40,
    "incorrect_upstream": 50,
    "wrong_branch": 60,
    "branch_diverged": 70,
    "branch_ahead": 80,
    "branch_behind": 90,
    "pull_strategy": 100,
    "staged_changes": 110,
    "tracked_changes": 120,
    "untracked_obstruction": 130,
}


@dataclass(frozen=True)
class RepoIssue:
    code: str
    summary: str
    detail: str


@dataclass(frozen=True)
class RepoDiagnosis:
    is_healthy: bool
    summary: str
    issues: tuple[RepoIssue, ...] = ()
    details: tuple[str, ...] = ()


def run_git_recover(repo_root: Path, *, apply: bool = False) -> int:
    diagnosis = diagnose_repo(repo_root)
    print(diagnosis.summary)
    for issue in diagnosis.issues:
        print(f"- {issue.summary}: {issue.detail}")
    for line in diagnosis.details:
        print(line)

    if diagnosis.is_healthy:
        return 0

    if not apply:
        print("Re-run with `./forum git-recover --apply` to attempt an automatic repair.")
        return 1

    repair = repair_checkout(repo_root, diagnosis)
    print(repair.summary)
    for line in repair.details:
        print(f"- {line}")
    return 0 if repair.succeeded else 1


@dataclass(frozen=True)
class RepairResult:
    succeeded: bool
    summary: str
    details: tuple[str, ...] = ()


def diagnose_repo(repo_root: Path) -> RepoDiagnosis:
    git_dir_result = git(repo_root, "rev-parse", "--git-dir")
    branch_result = git(repo_root, "rev-parse", "--abbrev-ref", "HEAD")
    status_result = git(repo_root, "status", "--porcelain=1", "--branch")
    upstream_result = git(repo_root, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}")

    if (
        git_dir_result.returncode != 0
        or branch_result.returncode != 0
        or status_result.returncode != 0
    ):
        return RepoDiagnosis(
            is_healthy=False,
            summary="Git recovery could not inspect the repository state.",
            details=_error_lines(git_dir_result, branch_result, status_result),
        )

    git_dir = resolve_git_dir(repo_root, git_dir_result.stdout.strip())
    branch_name = branch_result.stdout.strip()
    status_lines = [line.rstrip("\n") for line in status_result.stdout.splitlines()]
    status_header = status_lines[0] if status_lines else ""
    change_lines = status_lines[1:]
    upstream_name = upstream_result.stdout.strip() if upstream_result.returncode == 0 else None

    issues: list[RepoIssue] = []
    issues.extend(_detect_operation_issues(git_dir))
    if branch_name == "HEAD":
        issues.append(
            RepoIssue(
                code="detached_head",
                summary="Detached HEAD",
                detail="HEAD is detached and not attached to a local branch.",
            )
        )
    if upstream_name is None:
        issues.append(
            RepoIssue(
                code="missing_upstream",
                summary="Missing upstream",
                detail="The current branch does not track a remote branch.",
            )
        )
    elif upstream_name != TARGET_UPSTREAM:
        issues.append(
            RepoIssue(
                code="incorrect_upstream",
                summary="Incorrect upstream",
                detail=f"The current branch tracks `{upstream_name}` instead of `{TARGET_UPSTREAM}`.",
            )
        )
    if branch_name not in ("HEAD", TARGET_BRANCH):
        issues.append(
            RepoIssue(
                code="wrong_branch",
                summary="Wrong deployment branch",
                detail=f"The checkout is on `{branch_name}` instead of `{TARGET_BRANCH}`.",
            )
        )

    issues.extend(_detect_tracking_issues(repo_root, upstream_name))
    issues.extend(_detect_pull_strategy_issues(repo_root))
    issues.extend(_detect_worktree_issues(change_lines))

    issues = sorted(issues, key=lambda issue: ISSUE_ORDER[issue.code])
    if not issues:
        return RepoDiagnosis(
            is_healthy=True,
            summary=(
                "Git checkout is healthy: on `main`, tracking `origin/main`, "
                "fast-forward-only pulls configured, and working tree clean."
            ),
            details=(f"Status: {status_header}",),
        )

    details = (
        f"Current branch: {branch_name}",
        f"Status: {status_header or '(unavailable)'}",
        f"Upstream: {upstream_name or '(none)'}",
    )
    return RepoDiagnosis(
        is_healthy=False,
        summary=f"Git checkout needs recovery review: {issues[0].summary.lower()}.",
        issues=tuple(issues),
        details=details,
    )


def repair_checkout(repo_root: Path, diagnosis: RepoDiagnosis) -> RepairResult:
    guarded_issue_codes = {
        "branch_ahead",
        "branch_diverged",
        "staged_changes",
        "tracked_changes",
        "untracked_obstruction",
    }
    blocked_issue_codes = {
        "rebase_in_progress",
        "merge_in_progress",
    }
    issue_codes = {issue.code for issue in diagnosis.issues}
    if issue_codes & blocked_issue_codes:
        return RepairResult(
            succeeded=False,
            summary="Automatic repair stopped because a git operation is still in progress.",
            details=(
                "Resolve or abort the in-progress rebase/merge before running `./forum git-recover --apply` again.",
            ),
        )
    if issue_codes & guarded_issue_codes:
        return RepairResult(
            succeeded=False,
            summary="Automatic repair stopped to avoid discarding local work.",
            details=(
                "This checkout has local commits or local file changes that require explicit operator cleanup first.",
            ),
        )

    details: list[str] = []
    fetch_result = git(repo_root, "fetch", "origin")
    if fetch_result.returncode == 0:
        details.append("Fetched latest refs from `origin`.")
    elif "No such remote" in (fetch_result.stderr or ""):
        details.append("Skipped `git fetch origin` because no `origin` remote is configured.")
    else:
        return RepairResult(
            succeeded=False,
            summary="Automatic repair could not fetch `origin`.",
            details=_error_lines(fetch_result),
        )

    pull_ff = git(repo_root, "config", "pull.ff", TARGET_PULL_FF)
    if pull_ff.returncode != 0:
        return RepairResult(
            succeeded=False,
            summary="Automatic repair could not normalize pull strategy.",
            details=_error_lines(pull_ff),
        )
    details.append("Set local `pull.ff` to `only`.")

    target_remote_exists = git(repo_root, "show-ref", "--verify", "--quiet", f"refs/remotes/{TARGET_UPSTREAM}")
    target_remote_available = target_remote_exists.returncode == 0

    if target_remote_available:
        checkout_result = git(repo_root, "checkout", "-B", TARGET_BRANCH, TARGET_UPSTREAM)
        if checkout_result.returncode != 0:
            return RepairResult(
                succeeded=False,
                summary=f"Automatic repair could not reset `{TARGET_BRANCH}` to `{TARGET_UPSTREAM}`.",
                details=_error_lines(checkout_result),
            )
        details.append(f"Checked out `{TARGET_BRANCH}` and aligned it to `{TARGET_UPSTREAM}`.")

        upstream_result = git(repo_root, "branch", "--set-upstream-to", TARGET_UPSTREAM, TARGET_BRANCH)
        if upstream_result.returncode != 0:
            return RepairResult(
                succeeded=False,
                summary="Automatic repair could not restore branch upstream tracking.",
                details=_error_lines(upstream_result),
            )
        details.append(f"Set `{TARGET_BRANCH}` to track `{TARGET_UPSTREAM}`.")
    else:
        checkout_result = git(repo_root, "checkout", TARGET_BRANCH)
        if checkout_result.returncode != 0:
            return RepairResult(
                succeeded=False,
                summary=f"Automatic repair could not check out `{TARGET_BRANCH}`.",
                details=_error_lines(checkout_result),
            )
        details.append(f"Checked out existing local `{TARGET_BRANCH}`.")

    post_repair = diagnose_repo(repo_root)
    if not post_repair.is_healthy:
        detail_lines = list(details)
        detail_lines.append(post_repair.summary)
        for issue in post_repair.issues:
            detail_lines.append(f"{issue.summary}: {issue.detail}")
        return RepairResult(
            succeeded=False,
            summary="Automatic repair completed some steps but the checkout is still not healthy.",
            details=tuple(detail_lines),
        )

    details.append("Checkout is now healthy.")
    return RepairResult(
        succeeded=True,
        summary="Automatic repair completed successfully.",
        details=tuple(details),
    )


def _detect_operation_issues(git_dir: Path) -> list[RepoIssue]:
    issues: list[RepoIssue] = []
    if (git_dir / "rebase-merge").exists() or (git_dir / "rebase-apply").exists():
        issues.append(
            RepoIssue(
                code="rebase_in_progress",
                summary="Rebase in progress",
                detail="An interrupted rebase must be resolved or aborted before normal sync can continue.",
            )
        )
    if (git_dir / "MERGE_HEAD").exists():
        issues.append(
            RepoIssue(
                code="merge_in_progress",
                summary="Merge in progress",
                detail="An interrupted merge must be resolved or aborted before normal sync can continue.",
            )
        )
    return issues


def _detect_tracking_issues(repo_root: Path, upstream_name: str | None) -> list[RepoIssue]:
    if upstream_name is None:
        return []
    rev_list_result = git(repo_root, "rev-list", "--left-right", "--count", f"HEAD...{upstream_name}")
    if rev_list_result.returncode != 0:
        return []

    counts = rev_list_result.stdout.strip().split()
    if len(counts) != 2:
        return []

    ahead_count = int(counts[0])
    behind_count = int(counts[1])
    issues: list[RepoIssue] = []
    if ahead_count and behind_count:
        issues.append(
            RepoIssue(
                code="branch_diverged",
                summary="Branch diverged from upstream",
                detail=(
                    f"The current branch is {ahead_count} commit(s) ahead of and "
                    f"{behind_count} commit(s) behind `{upstream_name}`."
                ),
            )
        )
    elif ahead_count:
        issues.append(
            RepoIssue(
                code="branch_ahead",
                summary="Branch ahead of upstream",
                detail=f"The current branch has {ahead_count} local commit(s) not on `{upstream_name}`.",
            )
        )
    elif behind_count:
        issues.append(
            RepoIssue(
                code="branch_behind",
                summary="Branch behind upstream",
                detail=f"The current branch is {behind_count} commit(s) behind `{upstream_name}`.",
            )
        )
    return issues


def _detect_pull_strategy_issues(repo_root: Path) -> list[RepoIssue]:
    pull_ff = git(repo_root, "config", "--get", "pull.ff")
    pull_rebase = git(repo_root, "config", "--get", "pull.rebase")
    ff_value = pull_ff.stdout.strip() if pull_ff.returncode == 0 else ""
    rebase_value = pull_rebase.stdout.strip() if pull_rebase.returncode == 0 else ""

    if ff_value == TARGET_PULL_FF:
        return []

    detail = "Configured pull strategy does not enforce fast-forward-only pulls."
    if not ff_value and not rebase_value:
        detail = "No pull strategy is configured; future `git pull` may prompt or choose an unsafe default."
    elif rebase_value:
        detail = f"`pull.rebase` is set to `{rebase_value}` and `pull.ff` is `{ff_value or '(unset)'}`."
    elif ff_value and ff_value != TARGET_PULL_FF:
        detail = f"`pull.ff` is set to `{ff_value}` instead of `{TARGET_PULL_FF}`."

    return [
        RepoIssue(
            code="pull_strategy",
            summary="Pull strategy needs normalization",
            detail=detail,
        )
    ]


def _detect_worktree_issues(change_lines: list[str]) -> list[RepoIssue]:
    has_staged = False
    has_tracked = False
    has_untracked = False

    for line in change_lines:
        if not line:
            continue
        if line.startswith("??"):
            has_untracked = True
            continue
        if len(line) < 3:
            continue
        index_status = line[0]
        worktree_status = line[1]
        if index_status not in (" ", "?"):
            has_staged = True
        if worktree_status not in (" ", "?"):
            has_tracked = True

    issues: list[RepoIssue] = []
    if has_staged:
        issues.append(
            RepoIssue(
                code="staged_changes",
                summary="Staged but uncommitted changes",
                detail="The index contains staged changes that would be mixed into recovery steps.",
            )
        )
    if has_tracked:
        issues.append(
            RepoIssue(
                code="tracked_changes",
                summary="Tracked working-tree changes",
                detail="Tracked file edits are present in the working tree.",
            )
        )
    if has_untracked:
        issues.append(
            RepoIssue(
                code="untracked_obstruction",
                summary="Untracked-file obstruction risk",
                detail="Untracked files are present and may block checkout, merge, or reset steps.",
            )
        )
    return issues


def resolve_git_dir(repo_root: Path, git_dir_output: str) -> Path:
    git_dir = Path(git_dir_output)
    if git_dir.is_absolute():
        return git_dir
    return (repo_root / git_dir).resolve()


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
