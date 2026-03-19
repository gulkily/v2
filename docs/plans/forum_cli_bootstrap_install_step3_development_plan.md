1. Goal: make the `./forum` command surface reachable on a clean account before required Python packages are installed.
Dependencies: approved Step 2; current wrapper in `forum`; current task runner in `scripts/forum_tasks.py`; current env-loading helper in `forum_core/runtime_env.py`.
Expected changes: add one canonical bootstrap/install subcommand to the existing `./forum` task surface; adjust the startup/import boundary so bootstrap/help paths can run without crashing when install-time Python packages are missing; keep the direct `python3 scripts/forum_tasks.py ...` surface aligned with the same command contract. Planned contracts may include a dedicated task such as `forum install [...]` and a narrower runtime-env loading contract that can fail explicitly without aborting bootstrap-only commands.
Verification approach: from a clean disposable environment, confirm `./forum help` and the bootstrap/install command are reachable before installing requirements; confirm non-bootstrap runtime commands still report dependency/setup problems rather than pretending to succeed.
Risks or open questions:
- how explicit the bootstrap command should be about missing required modules for normal runtime commands
- whether any current top-level imports outside the env loader also need bootstrap-safe handling
Canonical components/API contracts touched: `./forum`; `python3 scripts/forum_tasks.py ...`; `forum_core.runtime_env` bootstrap/load behavior only.

2. Goal: support both install targets through the canonical bootstrap flow without forcing `.venv`.
Dependencies: Stage 1.
Expected changes: define the bootstrap command’s operator-facing install choices so it can install requirements either into a repo-local `.venv` or into the user-profile/global Python environment; preserve the existing wrapper preference for `.venv` when present without making `.venv` mandatory. Planned contracts may include flags or arguments that select install mode, but no new parallel installer entrypoint.
Verification approach: smoke-test both documented install shapes in disposable environments and confirm later `./forum` commands use whichever installed path is available as designed.
Risks or open questions:
- exact CLI wording for selecting install target while keeping the command simple
- whether user-profile/global installs should be the default or an explicit option
Canonical components/API contracts touched: `./forum` install command UX; existing wrapper interpreter-selection behavior in `forum`.

3. Goal: lock the bootstrap workflow into focused tests and operator documentation.
Dependencies: Stages 1-2; existing setup docs in `README.md` and `docs/developer_commands.md`; existing CLI/env tests in `tests/test_forum_tasks.py` and `tests/test_runtime_env.py`.
Expected changes: extend the targeted CLI/runtime-env test coverage for bootstrap-safe command access and install-mode selection; update the canonical setup docs so first-run guidance starts from `./forum` and documents both supported install shapes consistently.
Verification approach: run the focused test files, then manually follow the documented first-run flow to confirm the docs match the command surface.
Risks or open questions:
- keeping docs concise while still explaining the difference between user-profile/global installs and `.venv`
- avoiding drift between README setup steps and the developer command reference
Canonical components/API contracts touched: `README.md`; `docs/developer_commands.md`; `tests/test_forum_tasks.py`; `tests/test_runtime_env.py`.
