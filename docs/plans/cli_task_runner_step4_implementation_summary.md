## Stage 1 - Define the command contract
- Changes: Added `scripts/forum_tasks.py` as a contract-first reference runner skeleton with the canonical `forum` program name, registered `help`, `start`, and `test` subcommands, and separated argument parsing from task dispatch through `parse_task_args(...)` and `run_task(...)`.
- Verification: Ran `python3 scripts/forum_tasks.py`; ran `python3 scripts/forum_tasks.py help`; ran `python3 scripts/forum_tasks.py nope` and confirmed argparse rejects unknown subcommands with exit code `2`.
- Notes: `start` and `test` are intentionally placeholder commands at this stage so the public CLI shape is fixed before backend behavior is implemented.

## Stage 2 - Implement the Python reference runner
- Changes: Wired `scripts/forum_tasks.py` to the existing repo workflows by delegating `start` to `scripts/run_read_only.py` and `test` to `python3 -m unittest discover -s tests`, with optional test-pattern forwarding for focused runs.
- Verification: Ran `python3 scripts/forum_tasks.py help`; ran `python3 scripts/forum_tasks.py test test_profile_update_page.py` and confirmed the targeted unittest file passes; ran `env PYTHONUNBUFFERED=1 FORUM_PORT=8030 timeout 2s python3 scripts/forum_tasks.py start` and confirmed the server prints `Serving read-only forum on http://127.0.0.1:8030` before timeout.
- Notes: The server-start verification required an unsandboxed run because the sandbox blocks listening sockets; the command behavior itself was otherwise unchanged.

## Stage 3 - Add the repo-root wrapper
- Changes: Added the repo-root `forum` wrapper as the canonical short command and made it executable. The wrapper forwards argv to `scripts/forum_tasks.py` while preferring `.venv/bin/python3` when present and falling back to `python3` otherwise.
- Verification: Ran `./forum help`; ran `./forum test test_profile_update_page.py` and confirmed the targeted unittest file passes; ran `env PYTHONUNBUFFERED=1 FORUM_PORT=8031 timeout 2s ./forum start` and confirmed the wrapper reaches the local server path and prints `Serving read-only forum on http://127.0.0.1:8031` before timeout.
- Notes: The wrapper keeps the backend handoff intentionally small so a later Perl runner can be introduced behind the same public subcommands without changing the user-facing contract.

## Stage 4 - Document the command surface
- Changes: Added `docs/developer_commands.md` as the project-level command reference for `./forum`, including `help`, `start`, and `test` usage, the supported direct entrypoints, and the explicit rule that future backends such as Perl must preserve the same public contract.
- Verification: Reviewed `docs/developer_commands.md`; ran `./forum help` and confirmed the documented subcommands match the real help output; ran `./forum test test_profile_update_page.py` and confirmed the documented focused-test example works.
- Notes: This repo still has no broad root README, so the command reference lives in `docs/developer_commands.md` for now rather than expanding this feature into a general documentation overhaul.
