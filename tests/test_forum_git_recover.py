from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


def load_forum_git_recover_module():
    module_name = "forum_git_recover_test_module"
    script_path = Path(__file__).resolve().parent.parent / "scripts" / "forum_git_recover.py"
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ForumGitRecoverTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.module = load_forum_git_recover_module()

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def git(self, repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *args],
            cwd=repo,
            check=True,
            text=True,
            capture_output=True,
        )

    def git_allow_failure(self, repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *args],
            cwd=repo,
            check=False,
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
        seed = self.root / "seed"
        self.init_repo(seed)
        self.commit_file(seed, "base.txt", "base\n", "init")

        origin = self.root / "origin.git"
        self.git(seed, "init", "--bare", str(origin))
        self.git(seed, "remote", "add", "origin", str(origin))
        self.git(seed, "push", "-u", "origin", "main")

        clone = self.root / "clone"
        self.git(self.root, "clone", str(origin), str(clone))
        self.git(clone, "config", "user.email", "test@example.com")
        self.git(clone, "config", "user.name", "Test User")
        return origin, seed, clone

    def clone_origin(self, origin: Path, name: str) -> Path:
        clone = self.root / name
        self.git(self.root, "clone", str(origin), str(clone))
        self.git(clone, "config", "user.email", "test@example.com")
        self.git(clone, "config", "user.name", "Test User")
        return clone

    def issue_codes(self, diagnosis) -> list[str]:
        return [issue.code for issue in diagnosis.issues]

    def test_diagnose_repo_reports_healthy_checkout(self) -> None:
        origin, _, clone = self.setup_origin_clone()
        self.git(clone, "config", "pull.ff", "only")

        diagnosis = self.module.diagnose_repo(clone)

        self.assertTrue(diagnosis.is_healthy)
        self.assertEqual(diagnosis.issues, ())
        self.assertIn("healthy", diagnosis.summary)
        self.assertTrue(origin.exists())

    def test_diagnose_repo_reports_detached_head_and_rebase_marker(self) -> None:
        _, _, clone = self.setup_origin_clone()
        self.git(clone, "config", "pull.ff", "only")
        head_commit = self.git(clone, "rev-parse", "HEAD").stdout.strip()
        self.git(clone, "checkout", "--detach", head_commit)
        (clone / ".git" / "rebase-merge").mkdir()

        diagnosis = self.module.diagnose_repo(clone)

        self.assertFalse(diagnosis.is_healthy)
        self.assertEqual(self.issue_codes(diagnosis)[:2], ["rebase_in_progress", "detached_head"])

    def test_diagnose_repo_reports_merge_in_progress(self) -> None:
        _, _, clone = self.setup_origin_clone()
        self.git(clone, "config", "pull.ff", "only")
        merge_head = self.git(clone, "rev-parse", "HEAD").stdout.strip()
        (clone / ".git" / "MERGE_HEAD").write_text(f"{merge_head}\n", encoding="utf-8")

        diagnosis = self.module.diagnose_repo(clone)

        self.assertIn("merge_in_progress", self.issue_codes(diagnosis))

    def test_diagnose_repo_reports_missing_upstream_wrong_branch_and_pull_strategy(self) -> None:
        repo = self.root / "local"
        self.init_repo(repo)
        self.commit_file(repo, "file.txt", "x\n", "init")
        self.git(repo, "checkout", "-b", "feature")
        self.git(repo, "config", "pull.rebase", "true")

        diagnosis = self.module.diagnose_repo(repo)

        self.assertEqual(
            self.issue_codes(diagnosis)[:3],
            ["missing_upstream", "wrong_branch", "pull_strategy"],
        )

    def test_diagnose_repo_reports_incorrect_upstream(self) -> None:
        origin, seed, clone = self.setup_origin_clone()
        self.git(seed, "checkout", "-b", "feature")
        self.commit_file(seed, "feature.txt", "feature\n", "feature")
        self.git(seed, "push", "-u", "origin", "feature")
        self.git(clone, "fetch", "origin")
        self.git(clone, "branch", "--set-upstream-to=origin/feature", "main")
        self.git(clone, "config", "pull.ff", "only")

        diagnosis = self.module.diagnose_repo(clone)

        self.assertIn("incorrect_upstream", self.issue_codes(diagnosis))
        self.assertTrue(origin.exists())

    def test_diagnose_repo_reports_branch_behind(self) -> None:
        origin, _, clone = self.setup_origin_clone()
        updater = self.clone_origin(origin, "updater")
        self.git(clone, "config", "pull.ff", "only")
        self.commit_file(updater, "remote.txt", "remote\n", "remote update")
        self.git(updater, "push", "origin", "main")
        self.git(clone, "fetch", "origin")

        diagnosis = self.module.diagnose_repo(clone)

        self.assertIn("branch_behind", self.issue_codes(diagnosis))

    def test_diagnose_repo_reports_branch_ahead(self) -> None:
        _, _, clone = self.setup_origin_clone()
        self.git(clone, "config", "pull.ff", "only")
        self.commit_file(clone, "local.txt", "local\n", "local update")

        diagnosis = self.module.diagnose_repo(clone)

        self.assertIn("branch_ahead", self.issue_codes(diagnosis))

    def test_diagnose_repo_reports_branch_diverged(self) -> None:
        origin, _, clone = self.setup_origin_clone()
        updater = self.clone_origin(origin, "updater")
        self.git(clone, "config", "pull.ff", "only")
        self.commit_file(clone, "local.txt", "local\n", "local update")
        self.commit_file(updater, "remote.txt", "remote\n", "remote update")
        self.git(updater, "push", "origin", "main")
        self.git(clone, "fetch", "origin")

        diagnosis = self.module.diagnose_repo(clone)

        self.assertIn("branch_diverged", self.issue_codes(diagnosis))

    def test_diagnose_repo_reports_staged_tracked_and_untracked_changes(self) -> None:
        _, _, clone = self.setup_origin_clone()
        self.git(clone, "config", "pull.ff", "only")
        tracked_path = clone / "base.txt"
        tracked_path.write_text("modified\n", encoding="utf-8")
        self.git(clone, "add", "base.txt")
        tracked_path.write_text("modified again\n", encoding="utf-8")
        (clone / "scratch.txt").write_text("scratch\n", encoding="utf-8")

        diagnosis = self.module.diagnose_repo(clone)

        self.assertIn("staged_changes", self.issue_codes(diagnosis))
        self.assertIn("tracked_changes", self.issue_codes(diagnosis))
        self.assertIn("untracked_obstruction", self.issue_codes(diagnosis))

    def test_repair_checkout_recovers_detached_head_to_healthy_main(self) -> None:
        _, _, clone = self.setup_origin_clone()
        head_commit = self.git(clone, "rev-parse", "HEAD").stdout.strip()
        self.git(clone, "checkout", "--detach", head_commit)

        diagnosis = self.module.diagnose_repo(clone)
        repair = self.module.repair_checkout(clone, diagnosis)
        recovered = self.module.diagnose_repo(clone)

        self.assertTrue(repair.succeeded)
        self.assertTrue(recovered.is_healthy)
        self.assertEqual(self.git(clone, "branch", "--show-current").stdout.strip(), "main")
        self.assertEqual(self.git(clone, "config", "--get", "pull.ff").stdout.strip(), "only")

    def test_repair_checkout_restores_missing_upstream(self) -> None:
        origin, _, clone = self.setup_origin_clone()
        self.git(clone, "branch", "--unset-upstream")
        self.assertNotEqual(
            self.git_allow_failure(clone, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}").returncode,
            0,
        )
        diagnosis = self.module.diagnose_repo(clone)

        repair = self.module.repair_checkout(clone, diagnosis)
        recovered = self.module.diagnose_repo(clone)

        self.assertTrue(repair.succeeded)
        self.assertTrue(recovered.is_healthy)
        self.assertEqual(
            self.git(clone, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}").stdout.strip(),
            "origin/main",
        )
        self.assertTrue(origin.exists())

    def test_repair_checkout_fast_forwards_behind_branch(self) -> None:
        origin, _, clone = self.setup_origin_clone()
        updater = self.clone_origin(origin, "updater")
        self.commit_file(updater, "remote.txt", "remote\n", "remote update")
        self.git(updater, "push", "origin", "main")
        self.git(clone, "fetch", "origin")
        diagnosis = self.module.diagnose_repo(clone)

        repair = self.module.repair_checkout(clone, diagnosis)
        recovered = self.module.diagnose_repo(clone)

        self.assertTrue(repair.succeeded)
        self.assertTrue(recovered.is_healthy)
        self.assertEqual(self.git(clone, "rev-parse", "HEAD").stdout.strip(), self.git(clone, "rev-parse", "origin/main").stdout.strip())

    def test_repair_checkout_returns_to_main_from_clean_feature_branch(self) -> None:
        _, _, clone = self.setup_origin_clone()
        self.git(clone, "checkout", "-b", "feature")
        diagnosis = self.module.diagnose_repo(clone)

        repair = self.module.repair_checkout(clone, diagnosis)
        recovered = self.module.diagnose_repo(clone)

        self.assertTrue(repair.succeeded)
        self.assertTrue(recovered.is_healthy)
        self.assertEqual(self.git(clone, "branch", "--show-current").stdout.strip(), "main")

    def test_repair_checkout_blocks_branch_ahead_state(self) -> None:
        _, _, clone = self.setup_origin_clone()
        self.commit_file(clone, "local.txt", "local\n", "local update")
        diagnosis = self.module.diagnose_repo(clone)

        repair = self.module.repair_checkout(clone, diagnosis)

        self.assertFalse(repair.succeeded)
        self.assertIn("discarding local work", repair.summary)
        self.assertTrue(any("Branch ahead of upstream" in line for line in repair.details))

    def test_repair_checkout_blocks_branch_diverged_state(self) -> None:
        origin, _, clone = self.setup_origin_clone()
        updater = self.clone_origin(origin, "updater")
        self.commit_file(clone, "local.txt", "local\n", "local update")
        self.commit_file(updater, "remote.txt", "remote\n", "remote update")
        self.git(updater, "push", "origin", "main")
        self.git(clone, "fetch", "origin")
        diagnosis = self.module.diagnose_repo(clone)

        repair = self.module.repair_checkout(clone, diagnosis)

        self.assertFalse(repair.succeeded)
        self.assertTrue(any("Branch diverged from upstream" in line for line in repair.details))

    def test_repair_checkout_blocks_local_file_changes(self) -> None:
        _, _, clone = self.setup_origin_clone()
        tracked_path = clone / "base.txt"
        tracked_path.write_text("modified\n", encoding="utf-8")
        self.git(clone, "add", "base.txt")
        tracked_path.write_text("modified again\n", encoding="utf-8")
        (clone / "scratch.txt").write_text("scratch\n", encoding="utf-8")
        diagnosis = self.module.diagnose_repo(clone)

        repair = self.module.repair_checkout(clone, diagnosis)

        self.assertFalse(repair.succeeded)
        self.assertTrue(any("Staged but uncommitted changes" in line for line in repair.details))
        self.assertTrue(any("Tracked working-tree changes" in line for line in repair.details))
        self.assertTrue(any("Untracked-file obstruction risk" in line for line in repair.details))
