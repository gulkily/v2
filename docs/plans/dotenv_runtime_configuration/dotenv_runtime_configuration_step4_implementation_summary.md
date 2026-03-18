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

## Stage 3 - Runtime `.env` Loading And Missing-Key Notices
- Changes:
  - Added `notify_missing_env_defaults(...)` to `forum_core/runtime_env.py` with one-per-process warning suppression and a stable `./forum env-sync` operator hint.
  - Updated `scripts/run_read_only.py` to load repo-root `.env` before importing the WSGI application so `FORUM_HOST` and `FORUM_PORT` can come from `.env`.
  - Updated `forum_read_only/web.py` and `forum_cgi/entrypoint.py` to load `.env` and emit read-only missing-key notices on direct WSGI and CGI entrypoints.
  - Updated `scripts/forum_tasks.py` so the `test` subcommand loads `.env` and uses the same missing-key notice flow.
- Verification:
  - Ran `python3 -m py_compile forum_core/runtime_env.py scripts/forum_tasks.py scripts/run_read_only.py forum_read_only/web.py forum_cgi/entrypoint.py`.
  - Ran a disposable `.env` harness that imported `forum_read_only.web`, `forum_cgi.entrypoint`, `forum_cgi.posting`, and `forum_core.moderation`, confirming both read and write repo-root resolution came from `.env` and that the moderator allowlist resolved the `.env` fingerprint.
  - Ran a disposable `.env` harness around `./forum start` with `PYTHONUNBUFFERED=1` and confirmed the startup message used the `.env` host/port.
  - Ran a partial `.env` import harness for `forum_read_only.web` with logging enabled and confirmed the warning pointed to `./forum env-sync` while leaving `.env` unchanged.
- Notes:
  - Missing-key notices are intentionally read-only at runtime; only `./forum env-sync` mutates `.env`.

## Stage 4 - Tests And Operator Docs
- Changes:
  - Added `tests/test_runtime_env.py` covering missing-default parsing, append-only sync, non-overriding `.env` loading, and one-time warning behavior.
  - Added `tests/test_forum_tasks.py` covering `env-sync` argument parsing and the `run_env_sync()` create/no-op flows against a disposable repo root.
  - Updated `.env.example` to document `./forum env-sync`, no-overwrite semantics, env precedence, and restart expectations.
  - Updated `docs/developer_commands.md` to document `./forum env-sync`, automatic `.env` loading coverage, precedence rules, and restart expectations.
- Verification:
  - Ran `./forum test test_runtime_env.py`.
  - Ran `./forum test test_forum_tasks.py`.
  - Ran `./forum test test_profile_update_page.py` as a regression check on the env-aware web import path.
  - Ran `./forum help` and confirmed the documented `env-sync` subcommand still appears in the canonical CLI help surface.
- Notes:
  - With no local `.env`, `./forum test` currently surfaces the read-only missing-key warning before running the suite; this is expected and does not mutate repo state.
