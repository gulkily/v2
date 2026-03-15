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
