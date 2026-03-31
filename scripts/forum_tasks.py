#!/usr/bin/env python3
"""Reference task runner for common repo commands."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
REQUIREMENTS_PATH = REPO_ROOT / "requirements.txt"
VENV_DIR = REPO_ROOT / ".venv"
VENV_PYTHON = VENV_DIR / "bin" / "python3"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from forum_git_recover import run_git_recover
from forum_content_purge import run_content_purge

from forum_core.php_native_reads import rebuild_php_native_thread_snapshots
from forum_core.post_index import rebuild_post_index
from forum_core.runtime_env import (
    dotenv_available,
    get_missing_env_defaults,
    load_repo_env,
    notify_missing_env_defaults,
    repo_env_paths,
    sync_env_defaults,
)
from forum_core.php_host_setup import (
    PhpHostSetupRequest,
    default_php_host_static_html_dir,
    confirm_php_host_setup,
    load_php_host_runtime_config,
    publish_php_host_public_files,
    php_host_public_dir,
    php_host_config_path,
    resolve_public_web_root,
    resolve_php_host_setup_config,
    write_php_host_config,
)


@dataclass(frozen=True)
class TaskRequest:
    command: str
    install_target: str | None = None
    test_pattern: str | None = None
    git_recover_apply: bool = False
    git_upgrade_remote: str | None = None
    git_upgrade_branch: str | None = None
    content_purge_paths: tuple[str, ...] = ()
    content_purge_archive_output: str | None = None
    content_purge_apply: bool = False
    content_purge_force: bool = False
    rebuild_index_repo_root: str | None = None
    rebuild_php_native_repo_root: str | None = None
    rebuild_php_native_thread_ids: tuple[str, ...] = ()
    public_web_root: str | None = None
    app_root: str | None = None
    repo_root: str | None = None
    cache_dir: str | None = None
    non_interactive: bool = False
    php_host_refresh_config_path: str | None = None
    php_host_refresh_repo_root: str | None = None
    php_host_refresh_cache_dir: str | None = None
    php_host_refresh_static_html_dir: str | None = None
    php_host_refresh_skip_rebuild_index: bool = False


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="forum",
        description="Forum task runner.",
        epilog=(
            "Recent operator notes: `content-purge --apply` accepts `git-filter-repo` from PATH or "
            "`$HOME/.local/bin/git-filter-repo`; if the records tree was purged, new posts recreate the "
            "needed `records/...` directories automatically."
        ),
    )
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("help", help="Show help output.")
    install_parser = subparsers.add_parser(
        "install",
        help="Install required Python packages for this checkout.",
    )
    install_parser.add_argument(
        "--target",
        choices=("user", "venv", "current"),
        default="user",
        help="Install target: user profile (default), repo-local .venv, or the current Python environment.",
    )
    subparsers.add_parser("env-sync", help="Append missing .env settings from .env.example.")
    git_recover_parser = subparsers.add_parser(
        "git-recover",
        help="Diagnose and repair common deploy-checkout git state problems.",
    )
    git_recover_parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply a repair by resetting the checkout to the expected deployment state.",
    )
    git_upgrade_parser = subparsers.add_parser(
        "git-upgrade",
        help="Fetch and merge the latest upstream branch into the current local branch.",
    )
    git_upgrade_parser.add_argument(
        "--remote",
        default="origin",
        help="Remote to fetch from. Defaults to origin.",
    )
    git_upgrade_parser.add_argument(
        "--branch",
        default="main",
        help="Remote branch to merge. Defaults to main.",
    )
    content_purge_parser = subparsers.add_parser(
        "content-purge",
        help="Preview or apply archival-plus-history purge for selected records paths.",
        description=(
            "Preview or apply archival-plus-history purge for selected records paths. Apply mode requires "
            "`git-filter-repo`, discovered from PATH or `$HOME/.local/bin/git-filter-repo`."
        ),
    )
    content_purge_parser.add_argument(
        "paths",
        nargs="*",
        help="Canonical repository-backed content paths to archive and purge. Omit to use suggested defaults.",
    )
    content_purge_parser.add_argument(
        "--archive-output",
        help="Optional output path for the generated archive.",
    )
    content_purge_parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply the purge workflow instead of previewing it.",
    )
    content_purge_parser.add_argument(
        "--force",
        action="store_true",
        help="Allow the workflow to continue past future safety prompts when supported.",
    )
    rebuild_index_parser = subparsers.add_parser(
        "rebuild-index",
        help="Manually rebuild the derived post index.",
    )
    rebuild_index_parser.add_argument(
        "--repo-root",
        help="Override the forum data repository path. Defaults to the current checkout root.",
    )
    rebuild_php_native_parser = subparsers.add_parser(
        "rebuild-php-native-snapshots",
        help="Manually rebuild SQLite-backed PHP-native thread snapshots.",
    )
    rebuild_php_native_parser.add_argument(
        "thread_ids",
        nargs="*",
        help="Optional thread IDs to rebuild. Omit to rebuild all thread snapshots.",
    )
    rebuild_php_native_parser.add_argument(
        "--repo-root",
        help="Override the forum data repository path. Defaults to the current checkout root.",
    )
    php_host_parser = subparsers.add_parser(
        "php-host-setup",
        help="Generate PHP-host config and publish public files into a web root.",
    )
    php_host_parser.add_argument(
        "public_web_root",
        nargs="?",
        help="Target public web root for PHP-host files. Omit to be prompted interactively.",
    )
    php_host_parser.add_argument("--app-root", help="Override the deployed application checkout path.")
    php_host_parser.add_argument("--repo-root", help="Override the forum data repository path.")
    php_host_parser.add_argument("--cache-dir", help="Override the PHP cache directory path.")
    php_host_parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Use derived defaults and fail on invalid explicit values instead of prompting.",
    )
    php_host_refresh_parser = subparsers.add_parser(
        "php-host-refresh",
        help="Rebuild the post index and clear PHP-host caches.",
    )
    php_host_refresh_parser.add_argument(
        "--config-path",
        help="Override the PHP host config path. Defaults to php_host/public/forum_host_config.php.",
    )
    php_host_refresh_parser.add_argument(
        "--repo-root",
        help="Override the forum data repository path used for rebuild-index.",
    )
    php_host_refresh_parser.add_argument(
        "--cache-dir",
        help="Override the PHP microcache directory to clear.",
    )
    php_host_refresh_parser.add_argument(
        "--static-html-dir",
        help="Override the generated static HTML directory to clear.",
    )
    php_host_refresh_parser.add_argument(
        "--skip-rebuild-index",
        action="store_true",
        help="Clear caches only and skip the derived post-index rebuild.",
    )
    subparsers.add_parser("start", help="Start the local read-only forum server.")

    test_parser = subparsers.add_parser("test", help="Run the unittest suite.")
    test_parser.add_argument(
        "pattern",
        nargs="?",
        help="Optional unittest discovery pattern (example: test_profile_update_page.py).",
    )

    return parser


def parse_task_args(argv: list[str] | None = None) -> tuple[argparse.ArgumentParser, TaskRequest | None]:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command in (None, "help"):
        return parser, None
    if args.command == "install":
        return parser, TaskRequest(command="install", install_target=args.target)
    if args.command == "env-sync":
        return parser, TaskRequest(command="env-sync")
    if args.command == "git-recover":
        return parser, TaskRequest(command="git-recover", git_recover_apply=bool(args.apply))
    if args.command == "git-upgrade":
        return parser, TaskRequest(
            command="git-upgrade",
            git_upgrade_remote=args.remote,
            git_upgrade_branch=args.branch,
        )
    if args.command == "content-purge":
        return parser, TaskRequest(
            command="content-purge",
            content_purge_paths=tuple(args.paths),
            content_purge_archive_output=args.archive_output,
            content_purge_apply=bool(args.apply),
            content_purge_force=bool(args.force),
        )
    if args.command == "rebuild-index":
        return parser, TaskRequest(command="rebuild-index", rebuild_index_repo_root=args.repo_root)
    if args.command == "rebuild-php-native-snapshots":
        return parser, TaskRequest(
            command="rebuild-php-native-snapshots",
            rebuild_php_native_repo_root=args.repo_root,
            rebuild_php_native_thread_ids=tuple(args.thread_ids),
        )
    if args.command == "php-host-setup":
        return parser, TaskRequest(
            command="php-host-setup",
            public_web_root=args.public_web_root,
            app_root=args.app_root,
            repo_root=args.repo_root,
            cache_dir=args.cache_dir,
            non_interactive=bool(args.non_interactive),
        )
    if args.command == "php-host-refresh":
        return parser, TaskRequest(
            command="php-host-refresh",
            php_host_refresh_config_path=args.config_path,
            php_host_refresh_repo_root=args.repo_root,
            php_host_refresh_cache_dir=args.cache_dir,
            php_host_refresh_static_html_dir=args.static_html_dir,
            php_host_refresh_skip_rebuild_index=bool(args.skip_rebuild_index),
        )
    if args.command == "start":
        return parser, TaskRequest(command="start")
    if args.command == "test":
        return parser, TaskRequest(command="test", test_pattern=args.pattern)
    raise AssertionError(f"Unhandled command: {args.command}")


def run_task(request: TaskRequest) -> int:
    if request.command == "install":
        return run_install_for_target(request.install_target or "user")
    if request.command == "env-sync":
        return run_env_sync()
    if request.command == "git-recover":
        return run_git_recover(REPO_ROOT, apply=request.git_recover_apply)
    if request.command == "git-upgrade":
        return run_git_upgrade(
            remote_name=request.git_upgrade_remote or "origin",
            branch_name=request.git_upgrade_branch or "main",
        )
    if request.command == "content-purge":
        return run_content_purge(
            REPO_ROOT,
            paths=list(request.content_purge_paths),
            archive_output=(
                Path(request.content_purge_archive_output)
                if request.content_purge_archive_output
                else None
            ),
            dry_run=not request.content_purge_apply,
            force=request.content_purge_force,
        )
    if request.command == "rebuild-index":
        return run_rebuild_index(repo_root_text=request.rebuild_index_repo_root)
    if request.command == "rebuild-php-native-snapshots":
        return run_rebuild_php_native_snapshots(
            repo_root_text=request.rebuild_php_native_repo_root,
            thread_ids=request.rebuild_php_native_thread_ids,
        )
    if request.command == "php-host-setup":
        return run_php_host_setup(request)
    if request.command == "php-host-refresh":
        return run_php_host_refresh(request)
    if request.command == "start":
        return run_start()
    if request.command == "test":
        return run_tests(request.test_pattern)
    print(f"Unknown command: {request.command}", file=sys.stderr)
    return 1


def run_install_for_target(install_target: str) -> int:
    if not REQUIREMENTS_PATH.exists():
        print(f"Missing requirements file: {REQUIREMENTS_PATH}", file=sys.stderr)
        return 1
    if install_target == "venv":
        python_executable = ensure_repo_venv()
        target_label = f"repo-local virtual environment at {VENV_DIR}"
        command = [str(python_executable), "-m", "pip", "install", "-r", str(REQUIREMENTS_PATH)]
    elif install_target == "current":
        target_label = "current Python environment"
        command = [sys.executable, "-m", "pip", "install", "-r", str(REQUIREMENTS_PATH)]
    else:
        target_label = "user profile"
        command = [sys.executable, "-m", "pip", "install", "--user", "-r", str(REQUIREMENTS_PATH)]

    print(f"Installing Python requirements into the {target_label}...")
    result = subprocess.run(command, check=False, cwd=REPO_ROOT)
    if result.returncode != 0:
        return result.returncode
    print("Installation complete. Next steps: `./forum env-sync` then `./forum start`.")
    return 0


def ensure_repo_venv() -> Path:
    if VENV_PYTHON.exists():
        print(f"Using existing repo-local virtual environment: {VENV_DIR}")
        return VENV_PYTHON

    print(f"Creating repo-local virtual environment: {VENV_DIR}")
    result = subprocess.run(
        [sys.executable, "-m", "venv", str(VENV_DIR)],
        check=False,
        cwd=REPO_ROOT,
    )
    if result.returncode != 0:
        raise SystemExit(result.returncode)
    return VENV_PYTHON


def ensure_runtime_dependencies() -> bool:
    if dotenv_available():
        return True
    print(
        "Missing required Python module `python-dotenv`. Run `./forum install` first.",
        file=sys.stderr,
    )
    return False


def run_env_sync() -> int:
    env_path, env_example_path = repo_env_paths(REPO_ROOT)
    status = get_missing_env_defaults(env_path=env_path, env_example_path=env_example_path)
    if not status.get("example_found"):
        print(f"Missing defaults file: {env_example_path}", file=sys.stderr)
        return 1

    if int(status.get("missing_count", 0)) <= 0:
        print("No missing .env settings found. Nothing to sync.")
        return 0

    result = sync_env_defaults(env_path=env_path, env_example_path=env_example_path)
    if not result.get("updated"):
        print("No missing .env settings found. Nothing to sync.")
        return 0

    added_count = int(result.get("added_count", 0))
    if result.get("env_created"):
        print(f"Created .env and added {added_count} default setting(s) from .env.example.")
        return 0

    print(f"Added {added_count} missing setting(s) to .env from .env.example.")
    return 0


def run_start() -> int:
    if not ensure_runtime_dependencies():
        return 1
    command = [sys.executable, str(REPO_ROOT / "scripts/run_read_only.py")]
    return subprocess.run(command, check=False, cwd=REPO_ROOT).returncode


def run_git_command(*args: str, check: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        check=check,
        text=True,
        capture_output=True,
    )


def current_git_branch() -> str:
    result = run_git_command("branch", "--show-current")
    return result.stdout.strip()


def git_checkout_is_clean() -> tuple[bool, str]:
    status = run_git_command("status", "--short")
    if status.returncode != 0:
        return False, "Unable to read git status."
    if status.stdout.strip():
        return False, "Working tree is not clean; commit, stash, or remove local changes before upgrading."
    return True, ""


def git_operation_in_progress() -> str | None:
    git_dir_result = run_git_command("rev-parse", "--git-dir")
    if git_dir_result.returncode != 0:
        return "Unable to resolve git metadata directory."
    git_dir = Path(git_dir_result.stdout.strip())
    if not git_dir.is_absolute():
        git_dir = (REPO_ROOT / git_dir).resolve()
    if (git_dir / "MERGE_HEAD").exists():
        return "Merge in progress; resolve or abort it before upgrading."
    if (git_dir / "rebase-merge").exists() or (git_dir / "rebase-apply").exists():
        return "Rebase in progress; resolve or abort it before upgrading."
    return None


def run_git_upgrade(*, remote_name: str = "origin", branch_name: str = "main") -> int:
    branch = current_git_branch()
    if not branch:
        print("Detached HEAD; check out the local deployment branch before upgrading.", file=sys.stderr)
        return 1

    in_progress_message = git_operation_in_progress()
    if in_progress_message is not None:
        print(in_progress_message, file=sys.stderr)
        return 1

    is_clean, clean_message = git_checkout_is_clean()
    if not is_clean:
        print(clean_message, file=sys.stderr)
        return 1

    upstream_ref = f"{remote_name}/{branch_name}"
    print(f"Fetching {remote_name}...")
    fetch_result = run_git_command("fetch", remote_name)
    if fetch_result.returncode != 0:
        print(fetch_result.stderr.strip() or f"`git fetch {remote_name}` failed.", file=sys.stderr)
        return fetch_result.returncode

    print(f"Merging {upstream_ref} into local `{branch}`...")
    merge_result = run_git_command("merge", "--no-edit", upstream_ref)
    if merge_result.returncode != 0:
        print(merge_result.stderr.strip() or merge_result.stdout.strip() or f"`git merge {upstream_ref}` failed.", file=sys.stderr)
        return merge_result.returncode

    output = merge_result.stdout.strip()
    if output:
        print(output)
    print(f"Git upgrade complete: local `{branch}` now includes `{upstream_ref}`.")
    return 0


def run_rebuild_index(*, repo_root_text: str | None = None) -> int:
    repo_root = (Path(repo_root_text).expanduser() if repo_root_text else REPO_ROOT).resolve()
    rebuild_post_index(repo_root)
    print(f"Rebuilt post index for {repo_root}")
    return 0


def run_rebuild_php_native_snapshots(*, repo_root_text: str | None = None, thread_ids: tuple[str, ...] = ()) -> int:
    repo_root = (Path(repo_root_text).expanduser() if repo_root_text else REPO_ROOT).resolve()
    rebuilt = rebuild_php_native_thread_snapshots(
        repo_root,
        thread_ids=thread_ids if thread_ids else None,
    )
    scope_label = "all thread snapshots" if not thread_ids else ", ".join(thread_ids)
    print(f"Rebuilt PHP-native thread snapshots for {scope_label} in {repo_root}")
    print(f"Refreshed {len(rebuilt)} thread snapshot(s).")
    return 0


def clear_directory_contents(path: Path) -> tuple[int, int]:
    if not path.exists():
        return 0, 0
    removed_files = 0
    removed_dirs = 0
    for entry in sorted(path.iterdir(), key=lambda candidate: candidate.as_posix(), reverse=True):
        if entry.is_dir() and not entry.is_symlink():
            shutil.rmtree(entry)
            removed_dirs += 1
        else:
            entry.unlink()
            removed_files += 1
    return removed_files, removed_dirs


def run_php_host_refresh(request: TaskRequest) -> int:
    config_path = (
        Path(request.php_host_refresh_config_path).expanduser()
        if request.php_host_refresh_config_path
        else php_host_config_path(REPO_ROOT)
    )
    runtime_config = None
    if (
        request.php_host_refresh_repo_root is None
        or request.php_host_refresh_cache_dir is None
        or request.php_host_refresh_static_html_dir is None
    ):
        try:
            runtime_config = load_php_host_runtime_config(config_path)
        except ValueError as exc:
            if request.php_host_refresh_cache_dir is None and request.php_host_refresh_static_html_dir is None:
                print(str(exc), file=sys.stderr)
                return 1
            print(f"Warning: {exc}", file=sys.stderr)

    repo_root = (
        Path(request.php_host_refresh_repo_root).expanduser()
        if request.php_host_refresh_repo_root
        else runtime_config.repo_root if runtime_config and runtime_config.repo_root else REPO_ROOT
    ).resolve()
    cache_dir = (
        Path(request.php_host_refresh_cache_dir).expanduser()
        if request.php_host_refresh_cache_dir
        else runtime_config.cache_dir if runtime_config else None
    )
    static_html_dir = (
        Path(request.php_host_refresh_static_html_dir).expanduser()
        if request.php_host_refresh_static_html_dir
        else (
            runtime_config.static_html_dir
            if runtime_config and runtime_config.static_html_dir
            else default_php_host_static_html_dir(php_host_public_dir(REPO_ROOT))
        )
    )

    if cache_dir is None and static_html_dir is None:
        print(
            "No PHP-host cache paths were resolved. Configure `cache_dir` or `static_html_dir`, or pass overrides.",
            file=sys.stderr,
        )
        return 1

    print("PHP host refresh plan")
    print(f"- Config path: {config_path}")
    print(f"PHP host refresh target repo: {repo_root}")
    print(f"- Rebuild index: {'yes' if not request.php_host_refresh_skip_rebuild_index else 'no'}")
    print(f"- PHP microcache dir: {cache_dir if cache_dir is not None else 'not configured'}")
    print(f"- Static HTML dir: {static_html_dir}")

    if not request.php_host_refresh_skip_rebuild_index:
        print("Step 1/3: rebuilding derived post index...")
        rebuild_post_index(repo_root)
        print(f"Rebuilt post index for {repo_root}")
    else:
        print("Step 1/3: skipping derived post index rebuild.")

    if cache_dir is not None:
        print("Step 2/3: clearing PHP microcache...")
        removed_files, removed_dirs = clear_directory_contents(cache_dir)
        print(f"Cleared PHP microcache at {cache_dir} ({removed_files} files, {removed_dirs} directories removed).")
    else:
        print("Step 2/3: skipping PHP microcache clearing.")
        print("Skipped PHP microcache clearing because no cache_dir was configured.")

    print("Step 3/3: clearing generated static HTML artifacts...")
    removed_files, removed_dirs = clear_directory_contents(static_html_dir)
    print(
        f"Cleared static HTML artifacts at {static_html_dir} ({removed_files} files, {removed_dirs} directories removed)."
    )
    print("PHP host refresh complete.")
    return 0


def run_php_host_setup(request: TaskRequest) -> int:
    if not ensure_runtime_dependencies():
        return 1
    load_repo_env(repo_root=REPO_ROOT)
    setup_request = PhpHostSetupRequest(
        public_web_root=request.public_web_root,
        app_root=request.app_root,
        repo_root=request.repo_root,
        cache_dir=request.cache_dir,
        non_interactive=request.non_interactive,
    )
    try:
        existing_config = None
        config_path = php_host_config_path(REPO_ROOT)
        if config_path.exists():
            existing_config = load_php_host_runtime_config(config_path)
        public_web_root = resolve_public_web_root(
            request.public_web_root,
            existing_config=existing_config,
            non_interactive=request.non_interactive,
        )
        config = resolve_php_host_setup_config(
            setup_request,
            repo_root=REPO_ROOT,
            public_web_root=public_web_root,
            existing_config=existing_config,
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    interactive = not request.non_interactive and sys.stdin.isatty()
    if interactive and not confirm_php_host_setup(public_web_root, config):
        print("Cancelled php-host-setup.")
        return 1

    config_path = write_php_host_config(REPO_ROOT, config)
    linked, notes = publish_php_host_public_files(REPO_ROOT, public_web_root)

    print(f"Wrote PHP host config: {config_path}")
    print(f"App root: {config.app_root}")
    print(f"Forum repo root: {config.repo_root}")
    print(f"Cache dir: {config.cache_dir}")
    print(f"Static HTML dir: {config.static_html_dir}")
    if linked:
        for target, source in linked:
            print(f"Linked {target} -> {source}")
    else:
        print("No new symlinks were created.")
    for note in notes:
        print(note)
    return 0


def run_tests(test_pattern: str | None = None) -> int:
    if not ensure_runtime_dependencies():
        return 1
    load_repo_env(repo_root=REPO_ROOT)
    notify_missing_env_defaults(repo_root=REPO_ROOT)
    command = [sys.executable, "-m", "unittest", "discover", "-s", "tests"]
    if test_pattern:
        command.extend(["-p", test_pattern])
    return subprocess.run(command, check=False, cwd=REPO_ROOT).returncode


def main(argv: list[str] | None = None) -> int:
    parser, request = parse_task_args(argv)
    if request is None:
        parser.print_help()
        return 0
    return run_task(request)


if __name__ == "__main__":
    raise SystemExit(main())
