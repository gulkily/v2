from __future__ import annotations

import re
from pathlib import Path

from dotenv import load_dotenv


_ACTIVE_ASSIGNMENT_RE = re.compile(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=(.*)$")
_COMMENTED_ASSIGNMENT_RE = re.compile(
    r"^\s*#\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?!>)(.*)$"
)
REPO_ROOT = Path(__file__).resolve().parent.parent


def repo_env_paths(repo_root: Path | None = None) -> tuple[Path, Path]:
    root = (repo_root or REPO_ROOT).resolve()
    return root / ".env", root / ".env.example"


def parse_env_keys(lines: list[str]) -> list[str]:
    keys: list[str] = []
    seen: set[str] = set()
    for line in lines:
        match = _ACTIVE_ASSIGNMENT_RE.match(line)
        if not match:
            continue
        key = match.group(1)
        if key in seen:
            continue
        seen.add(key)
        keys.append(key)
    return keys


def _parse_default_entries(lines: list[str]) -> list[tuple[str, str]]:
    entries: list[tuple[str, str]] = []
    seen: set[str] = set()
    for line in lines:
        active_match = _ACTIVE_ASSIGNMENT_RE.match(line)
        commented_match = _COMMENTED_ASSIGNMENT_RE.match(line)
        match = active_match or commented_match
        if not match:
            continue
        key = match.group(1)
        if key in seen:
            continue
        seen.add(key)
        entries.append((key, match.group(2).strip()))
    return entries


def get_missing_env_defaults(
    env_path: Path,
    env_example_path: Path,
) -> dict[str, bool | int | list[str] | list[tuple[str, str]]]:
    if not env_example_path.exists():
        return {
            "example_found": False,
            "env_exists": env_path.exists(),
            "missing_count": 0,
            "missing_keys": [],
            "missing_entries": [],
        }

    env_example_lines = env_example_path.read_text(encoding="utf-8").splitlines()
    default_entries = _parse_default_entries(env_example_lines)
    if not default_entries:
        return {
            "example_found": True,
            "env_exists": env_path.exists(),
            "missing_count": 0,
            "missing_keys": [],
            "missing_entries": [],
        }

    env_exists = env_path.exists()
    current_content = env_path.read_text(encoding="utf-8") if env_exists else ""
    current_keys = set(parse_env_keys(current_content.splitlines()))
    missing_entries = [(key, value) for key, value in default_entries if key not in current_keys]
    return {
        "example_found": True,
        "env_exists": env_exists,
        "missing_count": len(missing_entries),
        "missing_keys": [key for key, _ in missing_entries],
        "missing_entries": missing_entries,
    }


def load_repo_env(*, repo_root: Path | None = None, override: bool = False) -> bool:
    env_path, _ = repo_env_paths(repo_root)
    return bool(load_dotenv(dotenv_path=env_path, override=override))
