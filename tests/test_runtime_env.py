from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from forum_core import runtime_env


class RuntimeEnvTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.tempdir.name)
        self.env_path, self.example_path = runtime_env.repo_env_paths(self.repo_root)
        runtime_env._NOTIFIED_MISSING_DEFAULTS.clear()

    def tearDown(self) -> None:
        self.tempdir.cleanup()
        runtime_env._NOTIFIED_MISSING_DEFAULTS.clear()

    def write_env(self, text: str) -> None:
        self.env_path.write_text(text, encoding="utf-8")

    def write_example(self, text: str) -> None:
        self.example_path.write_text(text, encoding="utf-8")

    def test_get_missing_env_defaults_ignores_plain_prose_comments(self) -> None:
        self.write_env("FORUM_PORT=9000\n")
        self.write_example(
            "\n".join(
                [
                    "# Optional bind host for the local server.",
                    "# FORUM_HOST=127.0.0.1",
                    "# Plain prose should stay ignored.",
                    "FORUM_PORT=8000",
                ]
            )
            + "\n"
        )

        status = runtime_env.get_missing_env_defaults(self.env_path, self.example_path)

        self.assertEqual(status["missing_keys"], ["FORUM_HOST"])
        self.assertEqual(status["missing_entries"], [("FORUM_HOST", "127.0.0.1")])

    def test_sync_env_defaults_creates_env_and_is_idempotent(self) -> None:
        self.write_example(
            "\n".join(
                [
                    "# FORUM_HOST=127.0.0.1",
                    "FORUM_PORT=8000",
                ]
            )
            + "\n"
        )

        first = runtime_env.sync_env_defaults(self.env_path, self.example_path)
        second = runtime_env.sync_env_defaults(self.env_path, self.example_path)
        synced = self.env_path.read_text(encoding="utf-8")

        self.assertTrue(first["updated"])
        self.assertTrue(first["env_created"])
        self.assertEqual(first["added_count"], 2)
        self.assertFalse(second["updated"])
        self.assertIn("# Added automatically from .env.example via ./forum env-sync.", synced)
        self.assertIn("FORUM_HOST=127.0.0.1", synced)
        self.assertIn("FORUM_PORT=8000", synced)

    def test_load_repo_env_preserves_existing_environment_values(self) -> None:
        self.write_env("FORUM_HOST=127.0.0.1\nFORUM_PORT=8000\n")

        with mock.patch.dict(os.environ, {"FORUM_PORT": "9000"}, clear=True):
            loaded = runtime_env.load_repo_env(repo_root=self.repo_root, override=False)

            self.assertTrue(loaded)
            self.assertEqual(os.environ["FORUM_HOST"], "127.0.0.1")
            self.assertEqual(os.environ["FORUM_PORT"], "9000")

    def test_load_repo_env_returns_false_when_python_dotenv_is_unavailable(self) -> None:
        self.write_env("FORUM_HOST=127.0.0.1\n")

        with mock.patch.object(runtime_env, "_load_dotenv", None):
            with mock.patch.dict(os.environ, {}, clear=True):
                loaded = runtime_env.load_repo_env(repo_root=self.repo_root, override=False)

        self.assertFalse(loaded)
        self.assertNotIn("FORUM_HOST", os.environ)

    def test_notify_missing_env_defaults_logs_once(self) -> None:
        self.write_env("FORUM_HOST=127.0.0.1\n")
        self.write_example(
            "\n".join(
                [
                    "# FORUM_HOST=127.0.0.1",
                    "FORUM_PORT=8000",
                ]
            )
            + "\n"
        )

        with self.assertLogs("forum_core.runtime_env", level="WARNING") as logs:
            first = runtime_env.notify_missing_env_defaults(repo_root=self.repo_root)
            second = runtime_env.notify_missing_env_defaults(repo_root=self.repo_root)

        self.assertTrue(first)
        self.assertFalse(second)
        self.assertEqual(len(logs.output), 1)
        self.assertIn("./forum env-sync", logs.output[0])

    def test_committed_env_example_includes_dedalus_api_key(self) -> None:
        committed_example_path = runtime_env.REPO_ROOT / ".env.example"

        status = runtime_env.get_missing_env_defaults(self.env_path, committed_example_path)

        self.assertTrue(status["example_found"])
        self.assertIn("DEDALUS_API_KEY", status["missing_keys"])
        self.assertIn("FORUM_ENABLE_THREAD_AUTO_REPLY", status["missing_keys"])
        self.assertIn("FORUM_ENABLE_ACCOUNT_MERGE", status["missing_keys"])


if __name__ == "__main__":
    unittest.main()
