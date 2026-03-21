from __future__ import annotations

import importlib.util
import io
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
        self.assertIn("'app_root' =>", config_text)
        self.assertIn("'repo_root' =>", config_text)
        self.assertIn("Generated by ./forum php-host-setup", config_text)
        self.assertTrue((self.repo_root / "state" / "php_host_cache").is_dir())
        self.assertTrue((public_root / "index.php").is_symlink())
        self.assertTrue((public_root / ".htaccess").is_symlink())
        self.assertTrue((public_root / "forum_host_config.php").is_symlink())
        self.assertIn("Wrote PHP host config", stdout.getvalue())

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


if __name__ == "__main__":
    unittest.main()
