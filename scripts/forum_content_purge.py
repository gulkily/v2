#!/usr/bin/env python3
"""Operator-facing preview boundary for archival and history purge workflows."""

from __future__ import annotations

from pathlib import Path


def run_content_purge(
    repo_root: Path,
    *,
    paths: list[str],
    archive_output: Path | None = None,
    dry_run: bool = True,
    force: bool = False,
) -> int:
    normalized_paths = tuple(path.strip() for path in paths if path.strip())
    if not normalized_paths:
        print("No content paths were provided for purge preview.")
        return 1

    print("Content purge workflow preview")
    print(f"Repository root: {repo_root}")
    print(f"Mode: {'preview' if dry_run else 'apply'}")
    if archive_output is not None:
        print(f"Archive output: {archive_output}")
    print("Selected paths:")
    for path in normalized_paths:
        print(f"- {path}")

    if force:
        print("Force flag recorded for later safety-gate stages.")

    if dry_run:
        print("Preview only: no archive was created and no history was rewritten.")
        return 0

    print("Apply mode is not implemented yet. Re-run without `--apply` for preview output.")
    return 1
