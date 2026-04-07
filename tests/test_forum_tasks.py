from __future__ import annotations

import importlib.util
import io
import subprocess
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock


def load_forum_tasks_module():
    module_name = "forum_tasks_test_module"
    script_path = Path(__file__).resolve().parent.parent / "scripts" / "forum_tasks.py"
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ForumTasksTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.tempdir.name)
        self.module = load_forum_tasks_module()
        self.original_root = self.module.REPO_ROOT
        self.module.REPO_ROOT = self.repo_root

    def tearDown(self) -> None:
        self.module.REPO_ROOT = self.original_root
        self.tempdir.cleanup()

    def write_example(self, text: str) -> None:
        (self.repo_root / ".env.example").write_text(text, encoding="utf-8")

    def git(self, repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *args],
            cwd=repo,
            check=check,
            text=True,
            capture_output=True,
        )

    def init_repo(self, repo: Path) -> None:
        repo.mkdir(parents=True, exist_ok=True)
        self.git(repo, "init", "-b", "main")
        self.git(repo, "config", "user.email", "test@example.com")
        self.git(repo, "config", "user.name", "Test User")

    def commit_file(self, repo: Path, relative_path: str, content: str, message: str) -> None:
        path = repo / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        self.git(repo, "add", relative_path)
        self.git(repo, "commit", "-m", message)

    def setup_origin_clone(self) -> tuple[Path, Path, Path]:
        seed = self.repo_root / "seed"
        self.init_repo(seed)
        self.commit_file(seed, "base.txt", "base\n", "init")

        origin = self.repo_root / "origin.git"
        self.git(seed, "init", "--bare", str(origin))
        self.git(seed, "remote", "add", "origin", str(origin))
        self.git(seed, "push", "-u", "origin", "main")

        clone = self.repo_root / "clone"
        self.git(self.repo_root, "clone", str(origin), str(clone))
        self.git(clone, "config", "user.email", "test@example.com")
        self.git(clone, "config", "user.name", "Test User")
        return origin, seed, clone

    def write_php_host_sources(self) -> None:
        public_dir = self.repo_root / "php_host" / "public"
        public_dir.mkdir(parents=True, exist_ok=True)
        (public_dir / "index.php").write_text("<?php\n", encoding="utf-8")
        (public_dir / ".htaccess").write_text("RewriteEngine On\n", encoding="utf-8")
        (public_dir / "forum_host_config.example.php").write_text("<?php\nreturn [];\n", encoding="utf-8")

    def test_parse_task_args_accepts_env_sync(self) -> None:
        _, request = self.module.parse_task_args(["env-sync"])

        self.assertIsNotNone(request)
        self.assertEqual(request.command, "env-sync")

    def test_parse_task_args_accepts_install_with_default_target(self) -> None:
        _, request = self.module.parse_task_args(["install"])

        self.assertIsNotNone(request)
        self.assertEqual(request.command, "install")
        self.assertEqual(request.install_target, "user")

    def test_parse_task_args_accepts_install_with_explicit_target(self) -> None:
        _, request = self.module.parse_task_args(["install", "--target", "venv"])

        self.assertIsNotNone(request)
        self.assertEqual(request.command, "install")
        self.assertEqual(request.install_target, "venv")

    def test_parse_task_args_accepts_git_recover(self) -> None:
        _, request = self.module.parse_task_args(["git-recover"])

        self.assertIsNotNone(request)
        self.assertEqual(request.command, "git-recover")
        self.assertFalse(request.git_recover_apply)

    def test_parse_task_args_accepts_git_recover_apply(self) -> None:
        _, request = self.module.parse_task_args(["git-recover", "--apply"])

        self.assertIsNotNone(request)
        self.assertEqual(request.command, "git-recover")
        self.assertTrue(request.git_recover_apply)

    def test_parse_task_args_accepts_git_upgrade(self) -> None:
        _, request = self.module.parse_task_args(["git-upgrade"])

        self.assertIsNotNone(request)
        self.assertEqual(request.command, "git-upgrade")
        self.assertEqual(request.git_upgrade_remote, "origin")
        self.assertEqual(request.git_upgrade_branch, "main")

    def test_parse_task_args_accepts_git_upgrade_overrides(self) -> None:
        _, request = self.module.parse_task_args(["git-upgrade", "--remote", "upstream", "--branch", "release"])

        self.assertIsNotNone(request)
        self.assertEqual(request.command, "git-upgrade")
        self.assertEqual(request.git_upgrade_remote, "upstream")
        self.assertEqual(request.git_upgrade_branch, "release")

    def test_parse_task_args_accepts_content_purge_preview(self) -> None:
        _, request = self.module.parse_task_args(["content-purge", "records/posts", "records/identity"])

        self.assertIsNotNone(request)
        self.assertEqual(request.command, "content-purge")
        self.assertEqual(request.content_purge_paths, ("records/posts", "records/identity"))
        self.assertFalse(request.content_purge_apply)
        self.assertFalse(request.content_purge_force)
        self.assertIsNone(request.content_purge_archive_output)

    def test_parse_task_args_accepts_content_purge_without_explicit_paths(self) -> None:
        _, request = self.module.parse_task_args(["content-purge"])

        self.assertIsNotNone(request)
        self.assertEqual(request.command, "content-purge")
        self.assertEqual(request.content_purge_paths, ())
        self.assertFalse(request.content_purge_apply)

    def test_parse_task_args_accepts_content_purge_apply_options(self) -> None:
        _, request = self.module.parse_task_args(
            [
                "content-purge",
                "records/posts",
                "--archive-output",
                "/tmp/archive.zip",
                "--apply",
                "--force",
            ]
        )

        self.assertIsNotNone(request)
        self.assertEqual(request.command, "content-purge")
        self.assertEqual(request.content_purge_paths, ("records/posts",))
        self.assertEqual(request.content_purge_archive_output, "/tmp/archive.zip")
        self.assertTrue(request.content_purge_apply)
        self.assertTrue(request.content_purge_force)

    def test_parse_task_args_accepts_rebuild_index(self) -> None:
        _, request = self.module.parse_task_args(["rebuild-index"])

        self.assertIsNotNone(request)
        self.assertEqual(request.command, "rebuild-index")
        self.assertIsNone(request.rebuild_index_repo_root)

    def test_parse_task_args_accepts_rebuild_index_repo_root_override(self) -> None:
        _, request = self.module.parse_task_args(["rebuild-index", "--repo-root", "/tmp/forum-data"])

        self.assertIsNotNone(request)
        self.assertEqual(request.command, "rebuild-index")
        self.assertEqual(request.rebuild_index_repo_root, "/tmp/forum-data")

    def test_parse_task_args_accepts_php_host_refresh(self) -> None:
        _, request = self.module.parse_task_args(
            [
                "php-host-refresh",
                "--config-path",
                "/tmp/forum_host_config.php",
                "--repo-root",
                "/tmp/forum-data",
                "--cache-dir",
                "/tmp/php-cache",
                "--static-html-dir",
                "/tmp/_static_html",
                "--skip-rebuild-index",
            ]
        )

        self.assertIsNotNone(request)
        self.assertEqual(request.command, "php-host-refresh")
        self.assertEqual(request.php_host_refresh_config_path, "/tmp/forum_host_config.php")
        self.assertEqual(request.php_host_refresh_repo_root, "/tmp/forum-data")
        self.assertEqual(request.php_host_refresh_cache_dir, "/tmp/php-cache")
        self.assertEqual(request.php_host_refresh_static_html_dir, "/tmp/_static_html")
        self.assertTrue(request.php_host_refresh_skip_rebuild_index)

    def test_run_env_sync_creates_env_from_example(self) -> None:
        self.write_example("# FORUM_HOST=127.0.0.1\nFORUM_PORT=8000\n")

        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = self.module.run_env_sync()

        synced = (self.repo_root / ".env").read_text(encoding="utf-8")
        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr.getvalue(), "")
        self.assertIn("Created .env and added 2 default setting(s) from .env.example.", stdout.getvalue())
        self.assertIn("FORUM_HOST=127.0.0.1", synced)
        self.assertIn("FORUM_PORT=8000", synced)

    def test_run_env_sync_reports_no_work_when_already_synced(self) -> None:
        self.write_example("# FORUM_HOST=127.0.0.1\n")
        (self.repo_root / ".env").write_text("FORUM_HOST=127.0.0.1\n", encoding="utf-8")

        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = self.module.run_env_sync()

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr.getvalue(), "")
        self.assertIn("No missing .env settings found. Nothing to sync.", stdout.getvalue())

    def test_run_install_for_target_uses_user_profile_by_default(self) -> None:
        requirements_path = self.repo_root / "requirements.txt"
        requirements_path.write_text("python-dotenv>=1,<2\n", encoding="utf-8")
        calls: list[list[str]] = []

        def fake_run(command: list[str], check: bool, cwd: Path) -> mock.Mock:
            del check
            self.assertEqual(cwd, self.repo_root)
            calls.append(command)
            return mock.Mock(returncode=0)

        stdout = io.StringIO()
        stderr = io.StringIO()
        with mock.patch.object(self.module, "REPO_ROOT", self.repo_root):
            with mock.patch.object(self.module, "REQUIREMENTS_PATH", requirements_path):
                with mock.patch.object(self.module.subprocess, "run", side_effect=fake_run):
                    with redirect_stdout(stdout), redirect_stderr(stderr):
                        exit_code = self.module.run_install_for_target("user")

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(
            calls,
            [[sys.executable, "-m", "pip", "install", "--user", "-r", str(requirements_path)]],
        )
        self.assertIn("user profile", stdout.getvalue())

    def test_run_install_for_target_can_create_repo_local_venv(self) -> None:
        requirements_path = self.repo_root / "requirements.txt"
        requirements_path.write_text("python-dotenv>=1,<2\n", encoding="utf-8")
        venv_dir = self.repo_root / ".venv"
        venv_python = venv_dir / "bin" / "python3"
        calls: list[list[str]] = []

        def fake_run(command: list[str], check: bool, cwd: Path) -> mock.Mock:
            del check
            self.assertEqual(cwd, self.repo_root)
            calls.append(command)
            if command[:3] == [sys.executable, "-m", "venv"]:
                venv_python.parent.mkdir(parents=True, exist_ok=True)
                venv_python.write_text("", encoding="utf-8")
            return mock.Mock(returncode=0)

        stdout = io.StringIO()
        stderr = io.StringIO()
        with mock.patch.object(self.module, "REPO_ROOT", self.repo_root):
            with mock.patch.object(self.module, "REQUIREMENTS_PATH", requirements_path):
                with mock.patch.object(self.module, "VENV_DIR", venv_dir):
                    with mock.patch.object(self.module, "VENV_PYTHON", venv_python):
                        with mock.patch.object(self.module.subprocess, "run", side_effect=fake_run):
                            with redirect_stdout(stdout), redirect_stderr(stderr):
                                exit_code = self.module.run_install_for_target("venv")

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(
            calls,
            [
                [sys.executable, "-m", "venv", str(venv_dir)],
                [str(venv_python), "-m", "pip", "install", "-r", str(requirements_path)],
            ],
        )
        self.assertIn("Creating repo-local virtual environment", stdout.getvalue())
        self.assertIn("repo-local virtual environment", stdout.getvalue())

    def test_run_task_dispatches_git_recover(self) -> None:
        request = self.module.TaskRequest(command="git-recover", git_recover_apply=True)

        with mock.patch.object(self.module, "run_git_recover", return_value=0) as mocked:
            exit_code = self.module.run_task(request)

        self.assertEqual(exit_code, 0)
        mocked.assert_called_once_with(self.repo_root, apply=True)

    def test_run_task_dispatches_git_upgrade(self) -> None:
        request = self.module.TaskRequest(command="git-upgrade", git_upgrade_remote="origin", git_upgrade_branch="main")

        with mock.patch.object(self.module, "run_git_upgrade", return_value=0) as mocked:
            exit_code = self.module.run_task(request)

        self.assertEqual(exit_code, 0)
        mocked.assert_called_once_with(remote_name="origin", branch_name="main")

    def test_run_git_upgrade_fetches_and_merges_origin_main(self) -> None:
        origin, seed, clone = self.setup_origin_clone()
        self.module.REPO_ROOT = clone
        self.commit_file(clone, "records/posts/local.txt", "local\n", "local content")
        self.commit_file(seed, "app.txt", "remote\n", "remote code")
        self.git(seed, "push", "origin", "main")

        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = self.module.run_git_upgrade()

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr.getvalue(), "")
        log_subjects = self.git(clone, "log", "--pretty=%s", "-3").stdout.strip().splitlines()
        self.assertIn("Merge remote-tracking branch 'origin/main'", log_subjects[0])
        self.assertTrue((clone / "records" / "posts" / "local.txt").exists())
        self.assertTrue((clone / "app.txt").exists())
        self.assertTrue(origin.exists())

    def test_run_git_upgrade_rejects_dirty_checkout(self) -> None:
        _, _, clone = self.setup_origin_clone()
        self.module.REPO_ROOT = clone
        (clone / "base.txt").write_text("changed\n", encoding="utf-8")

        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = self.module.run_git_upgrade()

        self.assertEqual(exit_code, 1)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("Working tree is not clean", stderr.getvalue())

    def test_run_git_upgrade_allows_ignored_static_html_artifacts(self) -> None:
        _, _, clone = self.setup_origin_clone()
        self.module.REPO_ROOT = clone
        exclude_path = clone / ".git" / "info" / "exclude"
        exclude_path.write_text("php_host/public/_static_html/\n", encoding="utf-8")
        static_path = clone / "php_host" / "public" / "_static_html" / "index.html"
        static_path.parent.mkdir(parents=True, exist_ok=True)
        static_path.write_text("<html></html>\n", encoding="utf-8")

        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = self.module.run_git_upgrade()

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr.getvalue(), "")
        self.assertIn("Git upgrade complete", stdout.getvalue())

    def test_run_task_dispatches_content_purge_preview(self) -> None:
        request = self.module.TaskRequest(
            command="content-purge",
            content_purge_paths=("records/posts", "records/identity"),
            content_purge_archive_output="/tmp/archive.zip",
            content_purge_apply=False,
            content_purge_force=True,
        )

        with mock.patch.object(self.module, "run_content_purge", return_value=0) as mocked:
            exit_code = self.module.run_task(request)

        self.assertEqual(exit_code, 0)
        mocked.assert_called_once_with(
            self.repo_root,
            paths=["records/posts", "records/identity"],
            archive_output=Path("/tmp/archive.zip"),
            dry_run=True,
            force=True,
        )

    def test_run_task_dispatches_rebuild_index(self) -> None:
        request = self.module.TaskRequest(command="rebuild-index", rebuild_index_repo_root="/tmp/forum-data")

        with mock.patch.object(self.module, "run_rebuild_index", return_value=0) as mocked:
            exit_code = self.module.run_task(request)

        self.assertEqual(exit_code, 0)
        mocked.assert_called_once_with(repo_root_text="/tmp/forum-data")

    def test_run_rebuild_index_rebuilds_post_index_for_current_repo_root(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()

        with mock.patch.object(self.module, "rebuild_post_index") as mocked:
            with redirect_stdout(stdout), redirect_stderr(stderr):
                exit_code = self.module.run_rebuild_index()

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr.getvalue(), "")
        mocked.assert_called_once_with(self.repo_root.resolve())
        self.assertIn("Rebuilt post index for", stdout.getvalue())

    def test_run_task_dispatches_php_host_refresh(self) -> None:
        request = self.module.TaskRequest(command="php-host-refresh", php_host_refresh_skip_rebuild_index=True)

        with mock.patch.object(self.module, "run_php_host_refresh", return_value=0) as mocked:
            exit_code = self.module.run_task(request)

        self.assertEqual(exit_code, 0)
        mocked.assert_called_once_with(request)

    def test_parse_task_args_accepts_php_host_setup(self) -> None:
        _, request = self.module.parse_task_args(["php-host-setup", "/tmp/public"])

        self.assertIsNotNone(request)
        self.assertEqual(request.command, "php-host-setup")
        self.assertEqual(request.public_web_root, "/tmp/public")

    def test_parse_task_args_accepts_php_host_setup_without_path(self) -> None:
        _, request = self.module.parse_task_args(["php-host-setup"])

        self.assertIsNotNone(request)
        self.assertEqual(request.command, "php-host-setup")
        self.assertIsNone(request.public_web_root)

    def test_run_php_host_setup_writes_config_and_symlinks(self) -> None:
        self.write_php_host_sources()
        public_root = self.repo_root / "public_html"

        stdout = io.StringIO()
        stderr = io.StringIO()
        request = self.module.TaskRequest(
            command="php-host-setup",
            public_web_root=str(public_root),
            non_interactive=True,
        )
        with redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = self.module.run_php_host_setup(request)

        config_path = self.repo_root / "php_host" / "public" / "forum_host_config.php"
        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr.getvalue(), "")
        self.assertTrue(config_path.exists())
        config_text = config_path.read_text(encoding="utf-8")
        self.assertIn(f"'public_web_root' => '{public_root.as_posix()}'", config_text)
        self.assertIn("'app_root' =>", config_text)
        self.assertIn("'repo_root' =>", config_text)
        self.assertIn("'static_html_dir' =>", config_text)
        self.assertIn("'site_title' => 'Forum Reader'", config_text)
        self.assertIn("Generated by ./forum php-host-setup", config_text)
        self.assertTrue((self.repo_root / "state" / "php_host_cache").is_dir())
        self.assertTrue((public_root / "_static_html").is_dir())
        self.assertTrue((public_root / "index.php").is_symlink())
        self.assertTrue((public_root / ".htaccess").is_symlink())
        self.assertTrue((public_root / "forum_host_config.php").is_symlink())
        self.assertIn("Wrote PHP host config", stdout.getvalue())
        self.assertIn("Static HTML dir:", stdout.getvalue())

    def test_run_php_host_setup_is_idempotent_on_rerun(self) -> None:
        self.write_php_host_sources()
        public_root = self.repo_root / "public_html"
        request = self.module.TaskRequest(
            command="php-host-setup",
            public_web_root=str(public_root),
            non_interactive=True,
        )

        first_stdout = io.StringIO()
        second_stdout = io.StringIO()
        with redirect_stdout(first_stdout), redirect_stderr(io.StringIO()):
            first_exit_code = self.module.run_php_host_setup(request)
        with redirect_stdout(second_stdout), redirect_stderr(io.StringIO()):
            second_exit_code = self.module.run_php_host_setup(request)

        self.assertEqual(first_exit_code, 0)
        self.assertEqual(second_exit_code, 0)
        self.assertTrue((public_root / "index.php").is_symlink())
        self.assertTrue((public_root / ".htaccess").is_symlink())
        self.assertTrue((public_root / "forum_host_config.php").is_symlink())
        self.assertIn("kept existing symlink", second_stdout.getvalue())

    def test_run_php_host_setup_non_interactive_uses_existing_public_web_root(self) -> None:
        self.write_php_host_sources()
        public_root = self.repo_root / "existing_public"
        config_path = self.repo_root / "php_host" / "public" / "forum_host_config.php"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(
            "\n".join(
                [
                    "<?php",
                    "",
                    "declare(strict_types=1);",
                    "",
                    "return [",
                    f"    'public_web_root' => {public_root.as_posix()!r},",
                    f"    'app_root' => {self.repo_root.as_posix()!r},",
                    f"    'repo_root' => {self.repo_root.as_posix()!r},",
                    f"    'cache_dir' => {(self.repo_root / 'state' / 'php_host_cache').as_posix()!r},",
                    f"    'static_html_dir' => {(public_root / '_static_html').as_posix()!r},",
                    "    'site_title' => 'zenmemes',",
                    "    'microcache_ttl' => 5,",
                    "];",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        stdout = io.StringIO()
        stderr = io.StringIO()
        request = self.module.TaskRequest(command="php-host-setup", non_interactive=True)

        with redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = self.module.run_php_host_setup(request)

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr.getvalue(), "")
        self.assertTrue((public_root / "index.php").is_symlink())
        self.assertTrue((public_root / ".htaccess").is_symlink())
        self.assertTrue((public_root / "forum_host_config.php").is_symlink())

    def test_run_php_host_setup_reuses_existing_config_values_on_rerun(self) -> None:
        self.write_php_host_sources()
        public_root = self.repo_root / "public_html"
        existing_app_root = self.repo_root / "existing_app"
        existing_repo_root = self.repo_root / "existing_repo"
        existing_cache_dir = self.repo_root / "existing_cache"
        existing_static_html_dir = self.repo_root / "existing_static_html"
        config_path = self.repo_root / "php_host" / "public" / "forum_host_config.php"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(
            "\n".join(
                [
                    "<?php",
                    "",
                    "declare(strict_types=1);",
                    "",
                    "return [",
                    f"    'public_web_root' => {public_root.as_posix()!r},",
                    f"    'app_root' => {existing_app_root.as_posix()!r},",
                    f"    'repo_root' => {existing_repo_root.as_posix()!r},",
                    f"    'cache_dir' => {existing_cache_dir.as_posix()!r},",
                    f"    'static_html_dir' => {existing_static_html_dir.as_posix()!r},",
                    "    'site_title' => 'zenmemes',",
                    "    'microcache_ttl' => 5,",
                    "];",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        request = self.module.TaskRequest(
            command="php-host-setup",
            public_web_root=str(public_root),
            non_interactive=True,
        )

        exit_code = self.module.run_php_host_setup(request)

        config_text = config_path.read_text(encoding="utf-8")
        self.assertEqual(exit_code, 0)
        self.assertIn(f"'app_root' => '{existing_app_root.as_posix()}'", config_text)
        self.assertIn(f"'repo_root' => '{existing_repo_root.as_posix()}'", config_text)
        self.assertIn(f"'cache_dir' => '{existing_cache_dir.as_posix()}'", config_text)
        self.assertIn(f"'static_html_dir' => '{existing_static_html_dir.as_posix()}'", config_text)
        self.assertIn("'site_title' => 'zenmemes'", config_text)

    def test_run_php_host_setup_prompts_interactively_when_path_missing(self) -> None:
        self.write_php_host_sources()
        public_root = self.repo_root / "interactive_public"
        answers = iter([str(public_root), "", "", "", ""])
        stdout = io.StringIO()
        stderr = io.StringIO()
        request = self.module.TaskRequest(command="php-host-setup")

        with mock.patch("builtins.input", side_effect=lambda prompt: next(answers)):
            with mock.patch("sys.stdin.isatty", return_value=True):
                with redirect_stdout(stdout), redirect_stderr(stderr):
                    exit_code = self.module.run_php_host_setup(request)

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr.getvalue(), "")
        self.assertTrue((public_root / "index.php").is_symlink())
        self.assertIn("PHP host setup will use:", stdout.getvalue())
        self.assertIn("Site title: Forum Reader", stdout.getvalue())

    def test_run_php_host_setup_interactive_defaults_show_existing_config_values(self) -> None:
        self.write_php_host_sources()
        public_root = self.repo_root / "interactive_public"
        stdout = io.StringIO()
        stderr = io.StringIO()
        existing_app_root = self.repo_root / "existing_app"
        existing_repo_root = self.repo_root / "existing_repo"
        existing_cache_dir = self.repo_root / "existing_cache"
        existing_static_html_dir = self.repo_root / "existing_static_html"
        config_path = self.repo_root / "php_host" / "public" / "forum_host_config.php"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(
            "\n".join(
                [
                    "<?php",
                    "",
                    "declare(strict_types=1);",
                    "",
                    "return [",
                    f"    'public_web_root' => {public_root.as_posix()!r},",
                    f"    'app_root' => {existing_app_root.as_posix()!r},",
                    f"    'repo_root' => {existing_repo_root.as_posix()!r},",
                    f"    'cache_dir' => {existing_cache_dir.as_posix()!r},",
                    f"    'static_html_dir' => {existing_static_html_dir.as_posix()!r},",
                    "    'site_title' => 'zenmemes',",
                    "    'microcache_ttl' => 5,",
                    "];",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        prompts: list[str] = []
        answers = iter([str(public_root), "", "", "", ""])
        request = self.module.TaskRequest(command="php-host-setup")

        def fake_input(prompt: str) -> str:
            prompts.append(prompt)
            return next(answers)

        with mock.patch("builtins.input", side_effect=fake_input):
            with mock.patch("sys.stdin.isatty", return_value=True):
                with redirect_stdout(stdout), redirect_stderr(stderr):
                    exit_code = self.module.run_php_host_setup(request)

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr.getvalue(), "")
        self.assertIn(f"Public web root path [{public_root}]: ", prompts)
        self.assertIn(f"Application checkout path [{existing_app_root}]: ", prompts)
        self.assertIn(f"Forum data repository path [{existing_repo_root}]: ", prompts)
        self.assertIn(f"PHP cache directory [{existing_cache_dir}]: ", prompts)
        self.assertIn("Site title: zenmemes", stdout.getvalue())

    def test_run_php_host_setup_uses_forum_site_title_env_in_generated_config(self) -> None:
        self.write_php_host_sources()
        public_root = self.repo_root / "public_html"
        request = self.module.TaskRequest(
            command="php-host-setup",
            public_web_root=str(public_root),
            non_interactive=True,
        )

        with mock.patch.dict("os.environ", {"FORUM_SITE_TITLE": "zenmemes"}, clear=False):
            exit_code = self.module.run_php_host_setup(request)

        config_path = self.repo_root / "php_host" / "public" / "forum_host_config.php"
        config_text = config_path.read_text(encoding="utf-8")
        self.assertEqual(exit_code, 0)
        self.assertIn("'site_title' => 'zenmemes'", config_text)

    def test_run_php_host_setup_env_site_title_overrides_existing_config_value(self) -> None:
        self.write_php_host_sources()
        public_root = self.repo_root / "public_html"
        config_path = self.repo_root / "php_host" / "public" / "forum_host_config.php"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(
            "\n".join(
                [
                    "<?php",
                    "",
                    "declare(strict_types=1);",
                    "",
                    "return [",
                    f"    'public_web_root' => {public_root.as_posix()!r},",
                    f"    'app_root' => {self.repo_root.as_posix()!r},",
                    f"    'repo_root' => {self.repo_root.as_posix()!r},",
                    f"    'cache_dir' => {(self.repo_root / 'state' / 'php_host_cache').as_posix()!r},",
                    f"    'static_html_dir' => {(public_root / '_static_html').as_posix()!r},",
                    "    'site_title' => 'Forum Reader',",
                    "    'microcache_ttl' => 5,",
                    "];",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        request = self.module.TaskRequest(command="php-host-setup", non_interactive=True)

        with mock.patch.dict("os.environ", {"FORUM_SITE_TITLE": "zenmemes"}, clear=False):
            exit_code = self.module.run_php_host_setup(request)

        config_text = config_path.read_text(encoding="utf-8")
        self.assertEqual(exit_code, 0)
        self.assertIn("'site_title' => 'zenmemes'", config_text)

    def test_run_php_host_setup_can_cancel_after_summary(self) -> None:
        self.write_php_host_sources()
        public_root = self.repo_root / "interactive_public"
        answers = iter([str(public_root), "", "", "", "n"])
        stdout = io.StringIO()
        stderr = io.StringIO()
        request = self.module.TaskRequest(command="php-host-setup")

        with mock.patch("builtins.input", side_effect=lambda prompt: next(answers)):
            with mock.patch("sys.stdin.isatty", return_value=True):
                with redirect_stdout(stdout), redirect_stderr(stderr):
                    exit_code = self.module.run_php_host_setup(request)

        self.assertEqual(exit_code, 1)
        self.assertEqual(stderr.getvalue(), "")
        self.assertFalse((public_root / "index.php").exists())
        self.assertIn("Cancelled php-host-setup.", stdout.getvalue())

    def test_run_php_host_refresh_rebuilds_index_and_clears_cache_paths(self) -> None:
        config_dir = self.repo_root / "php_host" / "public"
        config_dir.mkdir(parents=True, exist_ok=True)
        cache_dir = self.repo_root / "state" / "php_host_cache"
        static_html_dir = self.repo_root / "public_html" / "_static_html"
        cache_dir.mkdir(parents=True, exist_ok=True)
        static_html_dir.mkdir(parents=True, exist_ok=True)
        (cache_dir / "page.cgi").write_text("cached", encoding="utf-8")
        nested = static_html_dir / "threads" / "thread-1"
        nested.mkdir(parents=True, exist_ok=True)
        (nested / "index.html").write_text("<html></html>", encoding="utf-8")
        (config_dir / "forum_host_config.php").write_text(
            "\n".join(
                [
                    "<?php",
                    "return [",
                    f"    'repo_root' => {self.repo_root.as_posix()!r},",
                    f"    'cache_dir' => {cache_dir.as_posix()!r},",
                    f"    'static_html_dir' => {static_html_dir.as_posix()!r},",
                    "];",
                    "",
                ]
            ),
            encoding="utf-8",
        )

        stdout = io.StringIO()
        stderr = io.StringIO()
        request = self.module.TaskRequest(command="php-host-refresh")
        with mock.patch.object(self.module, "rebuild_post_index") as mocked_rebuild_index, mock.patch.object(
            self.module, "refresh_php_native_read_artifacts"
        ) as mocked_refresh_php_native, mock.patch.object(
            self.module, "rebuild_php_native_thread_snapshots",
            return_value=["thread-1"],
        ) as mocked_rebuild_php_native_threads:
            with redirect_stdout(stdout), redirect_stderr(stderr):
                exit_code = self.module.run_php_host_refresh(request)

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr.getvalue(), "")
        mocked_rebuild_index.assert_called_once_with(self.repo_root.resolve())
        mocked_refresh_php_native.assert_called_once_with(self.repo_root.resolve())
        mocked_rebuild_php_native_threads.assert_called_once_with(self.repo_root.resolve())
        self.assertTrue(cache_dir.is_dir())
        self.assertEqual(list(cache_dir.iterdir()), [])
        self.assertTrue(static_html_dir.is_dir())
        self.assertEqual(list(static_html_dir.iterdir()), [])
        self.assertIn("PHP host refresh plan", stdout.getvalue())
        self.assertIn("Step 1/4: rebuilding derived post index...", stdout.getvalue())
        self.assertIn("Step 2/4: rebuilding PHP-native read artifacts...", stdout.getvalue())
        self.assertIn("Step 3/4: resetting PHP microcache directory...", stdout.getvalue())
        self.assertIn("Step 4/4: clearing generated static HTML artifacts...", stdout.getvalue())
        self.assertIn("Reset PHP microcache directory", stdout.getvalue())
        self.assertIn("Cleared static HTML artifacts", stdout.getvalue())
        self.assertIn("Fallback recovery if stale PHP reads persist", stdout.getvalue())
        self.assertIn("PHP host refresh complete.", stdout.getvalue())

    def test_run_php_host_refresh_requires_resolvable_cache_paths(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()
        request = self.module.TaskRequest(command="php-host-refresh", php_host_refresh_config_path="/tmp/missing.php")

        with redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = self.module.run_php_host_refresh(request)

        self.assertEqual(exit_code, 1)
        self.assertIn("Missing PHP host config", stderr.getvalue())

    def test_run_php_host_refresh_uses_default_static_html_fallback_when_not_configured(self) -> None:
        config_dir = self.repo_root / "php_host" / "public"
        config_dir.mkdir(parents=True, exist_ok=True)
        cache_dir = self.repo_root / "state" / "php_host_cache"
        static_html_dir = config_dir / "_static_html"
        cache_dir.mkdir(parents=True, exist_ok=True)
        static_html_dir.mkdir(parents=True, exist_ok=True)
        (cache_dir / "page.cgi").write_text("cached", encoding="utf-8")
        (static_html_dir / "index.html").write_text("<html></html>", encoding="utf-8")
        (config_dir / "forum_host_config.php").write_text(
            "\n".join(
                [
                    "<?php",
                    "return [",
                    f"    'repo_root' => {self.repo_root.as_posix()!r},",
                    f"    'cache_dir' => {cache_dir.as_posix()!r},",
                    "];",
                    "",
                ]
            ),
            encoding="utf-8",
        )

        stdout = io.StringIO()
        stderr = io.StringIO()
        request = self.module.TaskRequest(command="php-host-refresh")
        with mock.patch.object(self.module, "rebuild_post_index") as mocked_rebuild_index, mock.patch.object(
            self.module, "refresh_php_native_read_artifacts"
        ) as mocked_refresh_php_native, mock.patch.object(
            self.module, "rebuild_php_native_thread_snapshots",
            return_value=[],
        ) as mocked_rebuild_php_native_threads:
            with redirect_stdout(stdout), redirect_stderr(stderr):
                exit_code = self.module.run_php_host_refresh(request)

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr.getvalue(), "")
        mocked_rebuild_index.assert_called_once_with(self.repo_root.resolve())
        mocked_refresh_php_native.assert_called_once_with(self.repo_root.resolve())
        mocked_rebuild_php_native_threads.assert_called_once_with(self.repo_root.resolve())
        self.assertTrue(cache_dir.is_dir())
        self.assertEqual(list(cache_dir.iterdir()), [])
        self.assertEqual(list(static_html_dir.iterdir()), [])
        self.assertIn("Step 4/4: clearing generated static HTML artifacts...", stdout.getvalue())
        self.assertIn(str(static_html_dir), stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
