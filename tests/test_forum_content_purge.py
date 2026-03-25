from __future__ import annotations

import importlib.util
import io
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock
import zipfile


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

    def test_suggest_default_purge_paths_prefers_known_content_families(self) -> None:
        self.write_text("records/moderation/mod-001.txt", "Record-ID: mod-001\n\nBody.\n")
        self.write_text("records/instance/public.txt", "keep this\n")
        self.write_text("records/system/key.asc", "secret\n")

        suggested = self.module.suggest_default_purge_paths(self.repo_root)

        self.assertEqual(
            suggested,
            (
                "records/posts",
                "records/identity",
                "records/moderation",
            ),
        )

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
        self.assertIn("Possible next commands:", output)
        self.assertIn("./forum content-purge records/posts records/identity --apply", output)
        self.assertFalse(archive_path.exists())
        self.assertFalse(archive_path.with_suffix(".manifest.txt").exists())

    def test_run_content_purge_preview_uses_suggested_defaults_when_paths_missing(self) -> None:
        archive_path = self.repo_root.parent / "default-preview.zip"
        stdout = io.StringIO()
        stderr = io.StringIO()

        with redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = self.module.run_content_purge(
                self.repo_root,
                paths=[],
                archive_output=archive_path,
                dry_run=True,
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr.getvalue(), "")
        output = stdout.getvalue()
        self.assertIn("No explicit paths were provided. Using suggested default paths", output)
        self.assertIn("- records/posts", output)
        self.assertIn("- records/identity", output)
        self.assertIn("./forum content-purge records --apply", output)

    def test_run_content_purge_preview_suggests_archive_output_and_force_when_needed(self) -> None:
        self.write_text("records/posts/untracked.txt", "Post-ID: untracked\n\nBody.\n")
        stdout = io.StringIO()
        stderr = io.StringIO()

        with redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = self.module.run_content_purge(
                self.repo_root,
                paths=["records/posts"],
                archive_output=None,
                dry_run=True,
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr.getvalue(), "")
        output = stdout.getvalue()
        self.assertIn("--archive-output /tmp/forum-content-purge.zip", output)
        self.assertIn("re-run apply with `--force`", output)

    def test_run_content_purge_preview_treats_records_root_as_default_alias(self) -> None:
        archive_path = self.repo_root.parent / "records-root-preview.zip"
        stdout = io.StringIO()
        stderr = io.StringIO()

        with redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = self.module.run_content_purge(
                self.repo_root,
                paths=["records"],
                archive_output=archive_path,
                dry_run=True,
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr.getvalue(), "")
        output = stdout.getvalue()
        self.assertIn("Using suggested default paths", output)
        self.assertIn("- records/posts", output)
        self.assertIn("- records/identity", output)

    def test_build_purge_plan_rejects_records_root_mixed_with_explicit_paths(self) -> None:
        with self.assertRaisesRegex(ValueError, "Use `records` by itself"):
            self.module.build_purge_plan(
                self.repo_root,
                requested_paths=["records", "records/posts"],
                archive_output=self.repo_root.parent / "mixed.zip",
            )

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

    def test_run_content_purge_apply_reports_missing_filter_repo(self) -> None:
        archive_path = self.repo_root.parent / "missing-tool.zip"
        stdout = io.StringIO()
        stderr = io.StringIO()

        with mock.patch.object(self.module.shutil, "which", return_value=None):
            with redirect_stdout(stdout), redirect_stderr(stderr):
                exit_code = self.module.run_content_purge(
                    self.repo_root,
                    paths=["records/posts"],
                    archive_output=archive_path,
                    dry_run=False,
                    force=False,
                )

        self.assertEqual(exit_code, 1)
        self.assertIn("git filter-repo", stderr.getvalue())
        self.assertIn("python3 -m pip install --user git-filter-repo", stderr.getvalue())
        self.assertIn("$HOME/.local/bin/git-filter-repo", stderr.getvalue())
        self.assertFalse(archive_path.exists())
        self.assertFalse(archive_path.with_suffix(".manifest.txt").exists())

    def test_ensure_filter_repo_available_falls_back_to_user_local_bin(self) -> None:
        fake_home = self.repo_root.parent / "fake-home"
        local_bin = fake_home / ".local" / "bin"
        local_bin.mkdir(parents=True, exist_ok=True)
        executable = local_bin / "git-filter-repo"
        executable.write_text("#!/bin/sh\nexit 0\n", encoding="ascii")
        executable.chmod(0o755)

        with mock.patch.object(self.module.shutil, "which", return_value=None):
            with mock.patch.object(self.module.Path, "home", return_value=fake_home):
                resolved = self.module.ensure_filter_repo_available(self.repo_root)

        self.assertEqual(resolved, executable)

    def test_run_content_purge_apply_rewrites_history_with_filter_repo_shim(self) -> None:
        archive_path = self.repo_root.parent / "apply-success.zip"
        shim_dir = self.repo_root.parent / "shim-bin"
        shim_dir.mkdir(parents=True, exist_ok=True)
        shim_path = shim_dir / "git-filter-repo"
        shim_path.write_text(
            "\n".join(
                [
                    "#!/bin/sh",
                    "set -eu",
                    "paths=\"\"",
                    "source_repo=\"\"",
                    "while [ \"$#\" -gt 0 ]; do",
                    "  case \"$1\" in",
                    "    --path) paths=\"$paths $2\"; shift 2 ;;",
                    "    --source) source_repo=\"$2\"; shift 2 ;;",
                    "    --force|--invert-paths) shift ;;",
                    "    *) shift ;;",
                    "  esac",
                    "done",
                    "if [ -z \"$paths\" ]; then",
                    "  echo \"missing paths\" >&2",
                    "  exit 1",
                    "fi",
                    "if [ -n \"$source_repo\" ]; then",
                    "  cd \"$source_repo\"",
                    "fi",
                    "git filter-branch --force --index-filter \"git rm -r --cached --ignore-unmatch $paths\" --prune-empty --tag-name-filter cat -- --all >/dev/null 2>&1",
                    "rm -rf .git/refs/original .git/logs/refs/original .git/filter-branch || true",
                    "git reflog expire --expire=now --all >/dev/null 2>&1 || true",
                    "git gc --prune=now >/dev/null 2>&1 || true",
                ]
            )
            + "\n",
            encoding="ascii",
        )
        shim_path.chmod(0o755)

        stdout = io.StringIO()
        stderr = io.StringIO()
        env_path = os.environ.get("PATH", "")
        with mock.patch.dict(os.environ, {"PATH": f"{shim_dir}:{env_path}"}):
            with redirect_stdout(stdout), redirect_stderr(stderr):
                exit_code = self.module.run_content_purge(
                    self.repo_root,
                    paths=["records/posts"],
                    archive_output=archive_path,
                    dry_run=False,
                    force=False,
                )

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr.getvalue(), "")
        self.assertTrue(archive_path.exists())
        self.assertTrue(archive_path.with_suffix(".manifest.txt").exists())
        with zipfile.ZipFile(archive_path) as archive:
            self.assertEqual(archive.namelist(), ["records/posts/root-001.txt"])
            archive_info = archive.getinfo("records/posts/root-001.txt")
            self.assertEqual(archive_info.date_time, (2020, 1, 1, 0, 0, 0))
            self.assertEqual(
                archive.read("records/posts/root-001.txt").decode("ascii"),
                "Post-ID: root-001\n\nBody.\n",
            )
        self.assertEqual(self.run_git("log", "--all", "--oneline", "--", "records/posts/root-001.txt"), "")
        self.assertIn("initial", self.run_git("log", "--all", "--oneline", "--", "README.md"))
        output = stdout.getvalue()
        self.assertIn("History rewrite completed for the selected paths.", output)
        self.assertIn("Required follow-up actions:", output)


if __name__ == "__main__":
    unittest.main()
