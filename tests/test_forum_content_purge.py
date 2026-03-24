from __future__ import annotations

import importlib.util
import io
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path


def load_forum_content_purge_module():
    module_name = "forum_content_purge_test_module"
    script_path = Path(__file__).resolve().parent.parent / "scripts" / "forum_content_purge.py"
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ForumContentPurgeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.tempdir.name)
        self.module = load_forum_content_purge_module()
        self.run_git("init")
        self.run_git("config", "user.name", "Test User")
        self.run_git("config", "user.email", "test@example.com")
        self.write_text("records/posts/root-001.txt", "Post-ID: root-001\n\nBody.\n")
        self.write_text("records/identity/identity-alpha.txt", "Record-ID: identity-alpha\n\nBody.\n")
        self.write_text("README.md", "keep me\n")
        self.run_git("add", ".")
        self.run_git("commit", "-m", "initial")

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def run_git(self, *args: str) -> str:
        result = subprocess.run(
            ["git", "-C", str(self.repo_root), *args],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return result.stdout.strip()

    def write_text(self, relative_path: str, text: str) -> Path:
        path = self.repo_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="ascii")
        return path

    def test_resolve_purge_paths_accepts_existing_records_directories(self) -> None:
        resolved = self.module.resolve_purge_paths(self.repo_root, ["records/posts", "records/identity"])

        self.assertEqual(
            resolved,
            (
                (self.repo_root / "records/identity").resolve(),
                (self.repo_root / "records/posts").resolve(),
            ),
        )

    def test_resolve_purge_paths_rejects_non_records_paths(self) -> None:
        with self.assertRaisesRegex(ValueError, "supported canonical content area"):
            self.module.resolve_purge_paths(self.repo_root, ["README.md"])

    def test_resolve_purge_paths_rejects_overlapping_paths(self) -> None:
        with self.assertRaisesRegex(ValueError, "Overlapping purge paths"):
            self.module.resolve_purge_paths(self.repo_root, ["records/posts", "records/posts/root-001.txt"])

    def test_run_content_purge_preview_reports_archive_and_manifest_targets(self) -> None:
        archive_path = self.repo_root.parent / "preview-output.zip"
        stdout = io.StringIO()
        stderr = io.StringIO()

        with redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = self.module.run_content_purge(
                self.repo_root,
                paths=["records/posts", "records/identity"],
                archive_output=archive_path,
                dry_run=True,
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr.getvalue(), "")
        output = stdout.getvalue()
        self.assertIn("Archive output:", output)
        self.assertIn(str(archive_path), output)
        self.assertIn("Manifest output:", output)
        self.assertIn("Archived file count: 2", output)
        self.assertIn("Preview only: no archive was created and no history was rewritten.", output)
        self.assertFalse(archive_path.exists())
        self.assertFalse(archive_path.with_suffix(".manifest.txt").exists())

    def test_run_content_purge_apply_refuses_dirty_worktree_without_force(self) -> None:
        self.write_text("records/posts/untracked.txt", "Post-ID: untracked\n\nBody.\n")
        archive_path = self.repo_root.parent / "apply-output.zip"
        stdout = io.StringIO()
        stderr = io.StringIO()

        with redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = self.module.run_content_purge(
                self.repo_root,
                paths=["records/posts"],
                archive_output=archive_path,
                dry_run=False,
                force=False,
            )

        self.assertEqual(exit_code, 1)
        self.assertIn("Refusing to apply content purge on a dirty worktree", stderr.getvalue())
        self.assertFalse(archive_path.exists())

    def test_build_archive_manifest_lists_selected_paths_and_files(self) -> None:
        plan = self.module.build_purge_plan(
            self.repo_root,
            requested_paths=["records/posts", "records/identity"],
            archive_output=self.repo_root.parent / "manifest-output.zip",
        )

        manifest = self.module.build_archive_manifest(plan, self.repo_root)

        self.assertIn("CONTENT-PURGE-MANIFEST/1", manifest)
        self.assertIn("Selected-Path-Count: 2", manifest)
        self.assertIn("- records/posts", manifest)
        self.assertIn("- records/identity", manifest)
        self.assertIn("- records/posts/root-001.txt", manifest)
        self.assertIn("- records/identity/identity-alpha.txt", manifest)


if __name__ == "__main__":
    unittest.main()
