## Stage 1
- Goal: define the canonical repo command contract and keep it separate from any one backend implementation.
- Dependencies: approved Step 2; current local server and test workflows.
- Expected changes: choose one repo-root executable name for the short command, define the first stable subcommand set (`help`, `start`, `test`), lock the expected high-level help/error/exit behavior, and add a backend-neutral dispatch boundary with planned helpers such as `parse_task_args(argv: list[str]) -> TaskRequest` and `run_task(request: TaskRequest) -> int`.
- Verification approach: invoke the reference runner directly with no args, `help`, and an unknown subcommand; confirm the help surface and exit behavior stay stable without touching existing direct scripts.
- Risks or open questions:
  - choosing too many first-slice subcommands and turning a small ergonomics feature into a general admin console
  - letting Python-specific CLI formatting become the canonical cross-implementation contract
- Canonical components/API contracts touched: repo-root task-command surface; stable subcommand/argument contract; direct script preservation rules.

## Stage 2
- Goal: implement the Python reference runner against the repo's existing common workflows.
- Dependencies: Stage 1.
- Expected changes: add one Python task-runner module under `scripts/` that implements the approved contract for `help`, `start`, and `test`; delegate `start` to the current local server path and `test` to the current unittest discovery path; planned helpers such as `run_start() -> int`, `run_tests(target: str | None = None) -> int`, and `main(argv: list[str] | None = None) -> int`.
- Verification approach: run the Python runner directly for `help`, `start`, and `test`, confirm it reaches `scripts/run_read_only.py` and the unittest suite successfully, and confirm the output remains short and predictable.
- Risks or open questions:
  - deciding whether the first `test` contract should stay minimal or allow one narrow target/pattern argument
  - keeping subprocess behavior straightforward enough that a later Perl runner can mirror it cleanly
- Canonical components/API contracts touched: `scripts/run_read_only.py`; unittest-based `tests/` workflow; Python reference implementation of the shared task-command contract.

## Stage 3
- Goal: add the short repo-root wrapper without hard-wiring the project to Python forever.
- Dependencies: Stage 2.
- Expected changes: add a small POSIX-compatible repo-root wrapper that forwards argv to the Python reference runner, keeps backend invocation logic narrow, and preserves room for a later Perl runner behind the same user-facing subcommands; direct CGI write commands remain untouched.
- Verification approach: run the repo-root command for `help`, `start`, and `test`, and confirm the wrapper preserves arguments and exit codes from the reference runner.
- Risks or open questions:
  - wrapper naming must be clear and short enough to become the canonical repo command
  - path and virtualenv resolution must stay simple so later side-by-side backend selection does not require a new public CLI shape
- Canonical components/API contracts touched: repo-root executable contract; backend-dispatch boundary; preservation of direct `cgi-bin/create_thread.py` and `cgi-bin/create_reply.py` usage.

## Stage 4
- Goal: document the new command as the canonical convenience surface while keeping lower-level entrypoints available.
- Dependencies: Stage 3.
- Expected changes: add or update one developer/operator doc that explains the repo-root command, the initial `help`/`start`/`test` workflow, the relationship to `scripts/run_read_only.py` and direct test invocation, and the rule that alternate backends such as Perl must preserve the same user-facing contract.
- Verification approach: follow the documented commands from a clean shell, cross-check them against the command help output, and confirm the docs still point to the direct underlying paths for debugging and parity work.
- Risks or open questions:
  - choosing the right documentation home in a repo that does not yet have a general setup/usage guide
  - keeping docs synchronized as new subcommands are added in later slices
- Canonical components/API contracts touched: developer/operator command documentation; stable command examples; explicit contract language for future Python/Perl parity.
