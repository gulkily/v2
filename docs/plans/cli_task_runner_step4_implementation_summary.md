## Stage 1 - Define the command contract
- Changes: Added `scripts/forum_tasks.py` as a contract-first reference runner skeleton with the canonical `forum` program name, registered `help`, `start`, and `test` subcommands, and separated argument parsing from task dispatch through `parse_task_args(...)` and `run_task(...)`.
- Verification: Ran `python3 scripts/forum_tasks.py`; ran `python3 scripts/forum_tasks.py help`; ran `python3 scripts/forum_tasks.py nope` and confirmed argparse rejects unknown subcommands with exit code `2`.
- Notes: `start` and `test` are intentionally placeholder commands at this stage so the public CLI shape is fixed before backend behavior is implemented.

## Stage 2 - Implement the Python reference runner
- Changes: Wired `scripts/forum_tasks.py` to the existing repo workflows by delegating `start` to `scripts/run_read_only.py` and `test` to `python3 -m unittest discover -s tests`, with optional test-pattern forwarding for focused runs.
- Verification: Ran `python3 scripts/forum_tasks.py help`; ran `python3 scripts/forum_tasks.py test test_profile_update_page.py` and confirmed the targeted unittest file passes; ran `env PYTHONUNBUFFERED=1 FORUM_PORT=8030 timeout 2s python3 scripts/forum_tasks.py start` and confirmed the server prints `Serving read-only forum on http://127.0.0.1:8030` before timeout.
- Notes: The server-start verification required an unsandboxed run because the sandbox blocks listening sockets; the command behavior itself was otherwise unchanged.
