## Stage 1 - Bootstrap-safe CLI entry and dependency boundary
- Changes:
  - Added an `install` subcommand to the existing `./forum` task surface for first-run package installation into the user profile.
  - Made `forum_core.runtime_env` tolerate a missing `python-dotenv` import so bootstrap-only command paths can still run.
  - Added an explicit runtime dependency check for `start` and `test` so they stop with a clear `./forum install` hint instead of silently running without required packages.
- Verification:
  - Ran `python3 -S scripts/forum_tasks.py help` and confirmed the CLI help loads without site-packages.
  - Ran `python3 -S scripts/forum_tasks.py start` and confirmed it exits with `Missing required Python module \`python-dotenv\`. Run \`./forum install\` first.`
  - Ran `python3 -S - <<'PY' ... importlib.util.find_spec('dotenv') ... PY` and confirmed the smoke environment had no `dotenv`.
- Notes:
  - `PYTHONNOUSERSITE=1` was insufficient here because this machine also has a system-wide `dotenv`; `python3 -S` was needed to simulate a truly clean import path.

## Stage 2 - Add selectable install targets
- Changes:
  - Extended `./forum install` with `--target {user,venv,current}` so operators can choose a user-profile install, a repo-local `.venv`, or the current Python environment.
  - Added repo-local virtual-environment creation for the `venv` target while preserving the wrapper’s existing preference for `.venv` when present.
  - Kept `user` as the default bootstrap target so a clean shell account does not have to create `.venv` unless the operator asks for it.
- Verification:
  - Ran `python3 -S scripts/forum_tasks.py install -h` and confirmed the target choices are exposed on the bootstrap-safe CLI surface.
  - Loaded `scripts/forum_tasks.py` directly with `importlib.util.spec_from_file_location(...)` and confirmed `parse_task_args(['install', '--target', <target>])` resolves `user`, `venv`, and `current` correctly.
  - Ran `./forum help` and confirmed the canonical wrapper still exposes `install` through the normal CLI flow.
- Notes:
  - A plain `import scripts.forum_tasks` smoke check was not reliable on this machine because an unrelated installed `scripts` package shadows the repo directory name on `sys.path`.

## Stage 3 - Tests, docs, and final verification
- Changes:
  - Added focused CLI tests for default and explicit install-target parsing plus user-profile and repo-local `.venv` install command execution paths.
  - Added runtime-env coverage for the missing-`python-dotenv` fallback path.
  - Updated `README.md` and `docs/developer_commands.md` so the canonical first-run setup flow starts with `./forum install` and documents `user`, `venv`, and `current` install targets.
- Verification:
  - Ran `python3 -m unittest /home/wsl/v2/tests/test_forum_tasks.py /home/wsl/v2/tests/test_runtime_env.py`.
  - Ran `./forum help`.
  - Ran `python3 -S scripts/forum_tasks.py help`.
  - Ran `python3 -S scripts/forum_tasks.py install -h`.
  - Ran `python3 -S scripts/forum_tasks.py start` and confirmed it prints the install hint instead of crashing at import time.
- Notes:
  - The final documented bootstrap flow now starts from `./forum install`, with `--target venv` available for operators who prefer an isolated repo-local interpreter.
