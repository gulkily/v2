## Stage 1 - Shared Env Catalog And Helper
- Changes:
  - Added `forum_core/runtime_env.py` with shared repo env path resolution, `.env.example` default parsing, missing-key analysis, and repo-root `.env` loading via `python-dotenv`.
  - Added the initial repo-root `.env.example` documenting `FORUM_MODERATOR_FINGERPRINTS`, `FORUM_REPO_ROOT`, `FORUM_HOST`, and `FORUM_PORT`.
  - Updated `.gitignore` to exclude the real `.env` file and added `requirements.txt` with `python-dotenv` as the minimal dependency for repo-root env loading.
- Verification:
  - Ran `python3 -m py_compile forum_core/runtime_env.py`.
  - Ran a temp-directory smoke script that exercised `repo_env_paths(...)` and `get_missing_env_defaults(...)`, confirming assignment-style defaults were detected while plain prose comments were ignored.
- Notes:
  - The dependency-location question from planning is resolved with a minimal `requirements.txt` because the repo did not already have an install manifest.

## Stage 2 - Add `./forum env-sync`
- Changes:
  - Extended `forum_core/runtime_env.py` with `sync_env_defaults(...)` and an append-only block builder for `.env.example` defaults.
  - Added an `env-sync` subcommand to `scripts/forum_tasks.py` with stable success/no-op/error messaging and `.env` creation when needed.
  - Updated the task runner import path setup so direct `python3 scripts/forum_tasks.py ...` execution can import shared repo modules cleanly.
- Verification:
  - Ran `python3 -m py_compile forum_core/runtime_env.py scripts/forum_tasks.py`.
  - Ran `./forum help` and confirmed `env-sync` appears in the canonical command help.
  - Ran a temp-directory smoke script that loaded `scripts/forum_tasks.py`, pointed `REPO_ROOT` at a disposable repo state, called `run_env_sync()` twice, and confirmed the first run created `.env` with only the missing keys while the second run reported that nothing remained to sync.
- Notes:
  - The sync helper currently inserts a marker comment before appended keys so later operator-added values remain visually distinct from synced defaults.
