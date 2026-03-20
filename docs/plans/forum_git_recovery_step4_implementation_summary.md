## Stage 1 - Wire `./forum git-recover`
- Changes:
  - Added the `git-recover` subcommand to [`scripts/forum_tasks.py`](/home/wsl/v2/scripts/forum_tasks.py) with `--apply` parsing and thin dispatch into a dedicated helper.
  - Added [`scripts/forum_git_recover.py`](/home/wsl/v2/scripts/forum_git_recover.py) with an initial diagnosis contract and a minimal healthy-state/no-op flow.
  - Extended [`tests/test_forum_tasks.py`](/home/wsl/v2/tests/test_forum_tasks.py) to cover CLI parsing and dispatch for the new subcommand.
- Verification:
  - Ran `./forum help`.
  - Ran `python3 -m unittest tests.test_forum_tasks`.
  - Ran `python3 -m unittest tests.test_forum_tasks -k git_recover`.
- Notes:
  - This stage intentionally stops at command wiring plus healthy-state handling; specific broken-state diagnosis and repairs land in later stages.

## Stage 2 - Diagnose supported broken states
- Changes:
  - Expanded [`scripts/forum_git_recover.py`](/home/wsl/v2/scripts/forum_git_recover.py) into a structured diagnosis model with ordered issue reporting for the supported high-likelihood states.
  - Added real disposable-repo coverage in [`tests/test_forum_git_recover.py`](/home/wsl/v2/tests/test_forum_git_recover.py) for healthy state, detached `HEAD`, rebase marker, merge marker, missing upstream, incorrect upstream, wrong branch, ahead/behind/diverged tracking, and staged/tracked/untracked local changes.
- Verification:
  - Ran `python3 -m unittest tests.test_forum_git_recover`.
  - Ran `python3 -m unittest tests.test_forum_tasks`.
- Notes:
  - This stage is diagnosis-only: the command can now classify the targeted states, but `--apply` still refuses to perform repairs until the later repair stages land.

## Stage 3 - Repair low-risk checkout states
- Changes:
  - Extended [`scripts/forum_git_recover.py`](/home/wsl/v2/scripts/forum_git_recover.py) with a repair path for low-risk states that can safely restore a clean deployment checkout.
  - The repair flow now fetches `origin` when available, normalizes local `pull.ff=only`, restores `main` against `origin/main`, and re-establishes upstream tracking for clean detached-head, behind-upstream, missing-upstream, incorrect-upstream, and clean wrong-branch cases.
  - Extended [`tests/test_forum_git_recover.py`](/home/wsl/v2/tests/test_forum_git_recover.py) to cover detached-head recovery, missing-upstream repair, behind-upstream fast-forward recovery, and clean branch return to `main`.
- Verification:
  - Ran `python3 -m unittest tests.test_forum_git_recover tests.test_forum_tasks`.
- Notes:
  - Rebase and merge states still stop for manual resolution in this stage.
  - Local commits or local file changes still block automatic cleanup until the destructive-state guardrail stage.

## Stage 4 - Guard destructive recovery states
- Changes:
  - Tightened [`scripts/forum_git_recover.py`](/home/wsl/v2/scripts/forum_git_recover.py) so risky states now return deterministic guarded-refusal details instead of a generic failure.
  - Extended [`tests/test_forum_git_recover.py`](/home/wsl/v2/tests/test_forum_git_recover.py) to cover guarded refusal for ahead-of-upstream, diverged, and local staged/tracked/untracked-change states.
- Verification:
  - Ran `python3 -m unittest tests.test_forum_git_recover tests.test_forum_tasks`.
- Notes:
  - The command still does not offer a destructive opt-in flag in this slice; operators must clean up or intentionally discard risky local state themselves before rerunning `--apply`.

## Stage 5 - Document and verify the operator workflow
- Changes:
  - Updated [`docs/developer_commands.md`](/home/wsl/v2/docs/developer_commands.md) to document `./forum git-recover`, `--apply`, the supported clean auto-repair states, and the guarded refusal cases.
  - Updated [`README.md`](/home/wsl/v2/README.md) so `git-recover` appears in the common command list.
- Verification:
  - Ran `python3 -m unittest tests.test_forum_git_recover tests.test_forum_tasks`.
  - Ran `./forum git-recover` from the current feature branch and confirmed it reports the branch/upstream/dirty-worktree blockers through the normal CLI path.
- Notes:
  - The CLI smoke run was intentionally executed from the active feature branch, so the non-healthy diagnosis was the expected result.
