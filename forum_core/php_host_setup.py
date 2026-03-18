from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


CONFIG_FILENAME = "forum_host_config.php"
CONFIG_EXAMPLE_FILENAME = "forum_host_config.example.php"
PUBLIC_FILENAMES = ("index.php", ".htaccess", CONFIG_FILENAME)


@dataclass(frozen=True)
class PhpHostSetupRequest:
    public_web_root: str
    app_root: str | None = None
    repo_root: str | None = None
    cache_dir: str | None = None
    non_interactive: bool = False


@dataclass(frozen=True)
class PhpHostSetupConfig:
    app_root: Path
    repo_root: Path
    cache_dir: Path


def php_host_public_dir(repo_root: Path) -> Path:
    return repo_root / "php_host" / "public"


def php_host_config_path(repo_root: Path) -> Path:
    return php_host_public_dir(repo_root) / CONFIG_FILENAME


def php_host_config_example_path(repo_root: Path) -> Path:
    return php_host_public_dir(repo_root) / CONFIG_EXAMPLE_FILENAME


def default_php_host_repo_root(repo_root: Path) -> Path:
    configured = os.environ.get("FORUM_REPO_ROOT", "").strip()
    if configured:
        return Path(configured).expanduser()
    return repo_root


def default_php_host_cache_dir(repo_root: Path) -> Path:
    configured = os.environ.get("FORUM_PHP_CACHE_DIR", "").strip()
    if configured:
        return Path(configured).expanduser()
    return default_php_host_repo_root(repo_root) / "state" / "php_host_cache"


def _normalize_path(raw_value: str) -> Path:
    return Path(raw_value).expanduser().resolve()


def _resolve_config_path(
    label: str,
    configured_value: str | None,
    *,
    default_path: Path,
    non_interactive: bool,
    input_func: Callable[[str], str],
) -> Path:
    if configured_value is not None:
        stripped = configured_value.strip()
        if stripped == "":
            raise ValueError(f"{label} cannot be empty.")
        return _normalize_path(stripped)

    if non_interactive:
        return default_path.resolve()

    prompt = f"{label} [{default_path}]: "
    entered = input_func(prompt).strip()
    if entered == "":
        return default_path.resolve()
    return _normalize_path(entered)


def resolve_php_host_setup_config(
    request: PhpHostSetupRequest,
    *,
    repo_root: Path,
    input_func: Callable[[str], str] = input,
) -> PhpHostSetupConfig:
    app_root = _resolve_config_path(
        "Application checkout path",
        request.app_root,
        default_path=repo_root,
        non_interactive=request.non_interactive,
        input_func=input_func,
    )
    forum_repo_root = _resolve_config_path(
        "Forum data repository path",
        request.repo_root,
        default_path=default_php_host_repo_root(repo_root),
        non_interactive=request.non_interactive,
        input_func=input_func,
    )
    cache_dir = _resolve_config_path(
        "PHP cache directory",
        request.cache_dir,
        default_path=default_php_host_cache_dir(repo_root),
        non_interactive=request.non_interactive,
        input_func=input_func,
    )
    return PhpHostSetupConfig(
        app_root=app_root,
        repo_root=forum_repo_root,
        cache_dir=cache_dir,
    )


def render_php_host_config(config: PhpHostSetupConfig) -> str:
    return "\n".join(
        [
            "<?php",
            "",
            "declare(strict_types=1);",
            "",
            "return [",
            f"    'app_root' => {config.app_root.as_posix()!r},",
            f"    'repo_root' => {config.repo_root.as_posix()!r},",
            f"    'cache_dir' => {config.cache_dir.as_posix()!r},",
            "    'microcache_ttl' => 5,",
            "];",
            "",
        ]
    )


def write_php_host_config(repo_root: Path, config: PhpHostSetupConfig) -> Path:
    config_path = php_host_config_path(repo_root)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(render_php_host_config(config), encoding="utf-8")
    return config_path


def ensure_public_web_root(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def publish_php_host_public_files(
    repo_root: Path,
    public_web_root: Path,
) -> tuple[list[tuple[Path, Path]], list[str]]:
    source_root = php_host_public_dir(repo_root)
    ensure_public_web_root(public_web_root)
    linked: list[tuple[Path, Path]] = []
    notes: list[str] = []

    for filename in PUBLIC_FILENAMES:
        source = source_root / filename
        target = public_web_root / filename
        if target.is_symlink():
            resolved = target.resolve(strict=False)
            if resolved == source.resolve():
                notes.append(f"kept existing symlink {target} -> {source}")
                continue
            target.unlink()
        elif target.exists():
            notes.append(
                f"left existing file in place at {target}; create a symlink to {source} manually if you want repo-managed updates"
            )
            continue

        try:
            target.symlink_to(source)
            linked.append((target, source))
        except OSError as exc:
            notes.append(
                f"could not symlink {target} -> {source} ({exc}); copy the file manually if this host does not allow symlinks"
            )
    return linked, notes
