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
