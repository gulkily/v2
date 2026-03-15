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


if __name__ == "__main__":
    unittest.main()
