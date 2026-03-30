from __future__ import annotations

import os
import re
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
    static_html_dir: Path
    site_title: str


@dataclass(frozen=True)
class PhpHostRuntimeConfig:
    app_root: Path | None
    repo_root: Path | None
    cache_dir: Path | None
    static_html_dir: Path | None
    site_title: str | None


def setup_prompt_value(
    label: str,
    *,
    default_value: str | Path | None = None,
    input_func: Callable[[str], str] | None = None,
) -> str:
    if input_func is None:
        input_func = input
    default_text = ""
    if default_value is not None:
        default_text = f" [{default_value}]"
    return input_func(f"{label}{default_text}: ").strip()


def resolve_public_web_root(
    configured_value: str | None,
    *,
    non_interactive: bool,
    input_func: Callable[[str], str] | None = None,
) -> Path:
    if configured_value is not None:
        stripped = configured_value.strip()
        if stripped == "":
            raise ValueError("Public web root cannot be empty.")
        return _normalize_path(stripped)

    if non_interactive:
        raise ValueError("Missing public web root path for php-host-setup.")

    entered = setup_prompt_value("Public web root path", input_func=input_func)
    if entered == "":
        raise ValueError("Public web root cannot be empty.")
    return _normalize_path(entered)


def confirm_php_host_setup(
    public_web_root: Path,
    config: PhpHostSetupConfig,
    *,
    input_func: Callable[[str], str] | None = None,
) -> bool:
    print("PHP host setup will use:")
    print(f"- Public web root: {public_web_root}")
    print(f"- Application checkout: {config.app_root}")
    print(f"- Forum data repository: {config.repo_root}")
    print(f"- PHP cache directory: {config.cache_dir}")
    print(f"- Static HTML directory: {config.static_html_dir}")
    print(f"- Site title: {config.site_title}")
    response = setup_prompt_value("Continue", default_value="Y/n", input_func=input_func).lower()
    return response in ("", "y", "yes")


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


def default_php_host_static_html_dir(public_web_root: Path) -> Path:
    return public_web_root / "_static_html"


def default_php_host_site_title() -> str:
    configured = os.environ.get("FORUM_SITE_TITLE", "").strip()
    if configured:
        return configured
    return "Forum Reader"


def _normalize_path(raw_value: str) -> Path:
    return Path(raw_value).expanduser().resolve()


def _resolve_config_path(
    label: str,
    configured_value: str | None,
    *,
    default_path: Path,
    non_interactive: bool,
    input_func: Callable[[str], str] | None,
) -> Path:
    if input_func is None:
        input_func = input
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
    public_web_root: Path,
    input_func: Callable[[str], str] | None = None,
) -> PhpHostSetupConfig:
    if input_func is None:
        input_func = input
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
    static_html_dir = default_php_host_static_html_dir(public_web_root)
    return PhpHostSetupConfig(
        app_root=app_root,
        repo_root=forum_repo_root,
        cache_dir=cache_dir,
        static_html_dir=static_html_dir,
        site_title=default_php_host_site_title(),
    )


def render_php_host_config(config: PhpHostSetupConfig) -> str:
    return "\n".join(
        [
            "<?php",
            "",
            "declare(strict_types=1);",
            "",
            "// Generated by ./forum php-host-setup. Edit host-local values here if needed.",
            "return [",
            f"    'app_root' => {config.app_root.as_posix()!r},",
            f"    'repo_root' => {config.repo_root.as_posix()!r},",
            f"    'cache_dir' => {config.cache_dir.as_posix()!r},",
            f"    'static_html_dir' => {config.static_html_dir.as_posix()!r},",
            f"    'site_title' => {config.site_title!r},",
            "    'microcache_ttl' => 5,",
            "];",
            "",
        ]
    )


def write_php_host_config(repo_root: Path, config: PhpHostSetupConfig) -> Path:
    config_path = php_host_config_path(repo_root)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config.cache_dir.mkdir(parents=True, exist_ok=True)
    config.static_html_dir.mkdir(parents=True, exist_ok=True)
    config_path.write_text(render_php_host_config(config), encoding="utf-8")
    return config_path


def load_php_host_runtime_config(config_path: Path) -> PhpHostRuntimeConfig:
    if not config_path.exists():
        raise ValueError(f"Missing PHP host config: {config_path}")

    text = config_path.read_text(encoding="utf-8")
    values = dict(re.findall(r"'([^']+)'\s*=>\s*'([^']*)'", text))

    def maybe_path(key: str) -> Path | None:
        value = values.get(key, "").strip()
        if value == "":
            return None
        return Path(value).expanduser()

    return PhpHostRuntimeConfig(
        app_root=maybe_path("app_root"),
        repo_root=maybe_path("repo_root"),
        cache_dir=maybe_path("cache_dir"),
        static_html_dir=maybe_path("static_html_dir"),
        site_title=values.get("site_title", "").strip() or None,
    )


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
        if not source.exists():
            notes.append(f"missing source file {source}; cannot publish {filename}")
            continue
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
