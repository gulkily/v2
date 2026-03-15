from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from textwrap import dedent
from unittest import mock

from forum_core.instance_info import (
    describe_moderation_settings,
    instance_info_path,
    load_instance_info,
    parse_instance_info_text,
    render_public_value,
)


class InstanceInfoTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.tempdir.name)
        subprocess.run(["git", "init"], cwd=self.repo_root, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=self.repo_root, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=self.repo_root, check=True)
        (self.repo_root / "README.md").write_text("fixture\n", encoding="utf-8")
        subprocess.run(["git", "add", "README.md"], cwd=self.repo_root, check=True)
        subprocess.run(["git", "commit", "-m", "initial"], cwd=self.repo_root, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def write_instance_info(self, text: str) -> None:
        path = instance_info_path(self.repo_root)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(dedent(text).lstrip(), encoding="utf-8")

    def test_parse_instance_info_text_requires_headers(self) -> None:
        with self.assertRaisesRegex(ValueError, "Admin-Contact"):
            parse_instance_info_text(
                "Instance-Name: Demo\nAdmin-Name: Operator\nRetention-Policy: keep\nInstall-Date: 2026-03-15\n\nsummary\n"
            )

    def test_load_instance_info_reads_tracked_and_git_derived_values(self) -> None:
        self.write_instance_info(
            """
            Instance-Name: Demo instance
            Admin-Name: Test operator
            Admin-Contact: operator@example.invalid
            Retention-Policy: Keep canonical records in git.
            Install-Date: 2026-03-15

            Short summary.
            """
        )

        with mock.patch.dict(os.environ, {"FORUM_MODERATOR_FINGERPRINTS": "ABCDEF0123456789"}, clear=False):
            info = load_instance_info(self.repo_root)

        self.assertEqual(info.instance_name, "Demo instance")
        self.assertEqual(info.admin_name, "Test operator")
        self.assertEqual(info.admin_contact, "operator@example.invalid")
        self.assertEqual(info.retention_policy, "Keep canonical records in git.")
        self.assertEqual(info.install_date, "2026-03-15")
        self.assertEqual(info.summary, "Short summary.")
        self.assertRegex(info.commit_id or "", r"^[0-9a-f]+$")
        self.assertTrue(info.commit_date)
        self.assertIn("1 configured moderator", info.moderation_settings)

    def test_load_instance_info_marks_missing_values_explicitly(self) -> None:
        info = load_instance_info(self.repo_root)

        self.assertEqual(info.source_path, instance_info_path(self.repo_root))
        self.assertEqual(render_public_value(info.instance_name), "Not published.")
        self.assertEqual(render_public_value(info.install_date), "Not published.")
        self.assertRegex(info.commit_id or "", r"^[0-9a-f]+$")

    def test_describe_moderation_settings_handles_empty_allowlist(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertIn("no moderator fingerprints are configured", describe_moderation_settings())


if __name__ == "__main__":
    unittest.main()
