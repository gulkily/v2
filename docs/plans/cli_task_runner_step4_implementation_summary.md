## Stage 1 - Define the command contract
- Changes: Added `scripts/forum_tasks.py` as a contract-first reference runner skeleton with the canonical `forum` program name, registered `help`, `start`, and `test` subcommands, and separated argument parsing from task dispatch through `parse_task_args(...)` and `run_task(...)`.
- Verification: Ran `python3 scripts/forum_tasks.py`; ran `python3 scripts/forum_tasks.py help`; ran `python3 scripts/forum_tasks.py nope` and confirmed argparse rejects unknown subcommands with exit code `2`.
- Notes: `start` and `test` are intentionally placeholder commands at this stage so the public CLI shape is fixed before backend behavior is implemented.
