from __future__ import annotations

import logging
import re
from pathlib import Path

try:
    from dotenv import load_dotenv as _load_dotenv
except ModuleNotFoundError:  # pragma: no cover - exercised through CLI bootstrap flow
    _load_dotenv = None


_ACTIVE_ASSIGNMENT_RE = re.compile(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=(.*)$")
_COMMENTED_ASSIGNMENT_RE = re.compile(
    r"^\s*#\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?!>)(.*)$"
)
REPO_ROOT = Path(__file__).resolve().parent.parent
_SYNC_NOTE = "# Added automatically from .env.example via ./forum env-sync."
logger = logging.getLogger(__name__)
_NOTIFIED_MISSING_DEFAULTS: set[tuple[Path, str]] = set()


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


def _build_missing_defaults_block(entries: list[tuple[str, str]]) -> str:
    lines = [_SYNC_NOTE]
    lines.extend(f"{key}={value}" for key, value in entries)
    return "\n".join(lines) + "\n"


def sync_env_defaults(env_path: Path, env_example_path: Path) -> dict[str, int | bool]:
    status = get_missing_env_defaults(env_path=env_path, env_example_path=env_example_path)
    if not status.get("example_found"):
        return {
            "example_found": False,
            "env_created": False,
            "added_count": 0,
            "updated": False,
        }

    env_exists = bool(status.get("env_exists"))
    missing_entries = list(status.get("missing_entries", []))
    if not missing_entries:
        return {
            "example_found": True,
            "env_created": False,
            "added_count": 0,
            "updated": False,
        }

    env_path.parent.mkdir(parents=True, exist_ok=True)
    current_content = env_path.read_text(encoding="utf-8") if env_exists else ""
    append_block = _build_missing_defaults_block(missing_entries)
    if current_content:
        if not current_content.endswith("\n"):
            current_content += "\n"
        current_content += "\n"
    next_content = current_content + append_block

    temp_path = env_path.with_name(f".{env_path.name}.tmp")
    try:
        temp_path.write_text(next_content, encoding="utf-8")
        temp_path.replace(env_path)
    finally:
        if temp_path.exists():
            temp_path.unlink()

    return {
        "example_found": True,
        "env_created": not env_exists,
        "added_count": len(missing_entries),
        "updated": True,
    }


def notify_missing_env_defaults(
    *,
    repo_root: Path | None = None,
    command_hint: str = "./forum env-sync",
) -> bool:
    env_path, env_example_path = repo_env_paths(repo_root)
    status = get_missing_env_defaults(env_path=env_path, env_example_path=env_example_path)
    if not status.get("example_found"):
        return False

    missing_count = int(status.get("missing_count", 0))
    if missing_count <= 0:
        return False

    notification_key = (env_path.resolve(), command_hint)
    if notification_key in _NOTIFIED_MISSING_DEFAULTS:
        return False
    _NOTIFIED_MISSING_DEFAULTS.add(notification_key)
    logger.warning(
        "Detected %s missing .env settings. Run `%s` to append defaults from .env.example.",
        missing_count,
        command_hint,
    )
    return True


def dotenv_available() -> bool:
    return _load_dotenv is not None


def load_repo_env(*, repo_root: Path | None = None, override: bool = False) -> bool:
    env_path, _ = repo_env_paths(repo_root)
    if _load_dotenv is None:
        return False
    return bool(_load_dotenv(dotenv_path=env_path, override=override))
