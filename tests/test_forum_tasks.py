from __future__ import annotations

import importlib.util
import io
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path


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

    def test_parse_task_args_accepts_php_host_setup(self) -> None:
        _, request = self.module.parse_task_args(["php-host-setup", "/tmp/public"])

        self.assertIsNotNone(request)
        self.assertEqual(request.command, "php-host-setup")
        self.assertEqual(request.public_web_root, "/tmp/public")

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
        self.assertTrue((public_root / "index.php").is_symlink())
        self.assertTrue((public_root / ".htaccess").is_symlink())
        self.assertTrue((public_root / "forum_host_config.php").is_symlink())
        self.assertIn("Wrote PHP host config", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
