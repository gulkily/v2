## Problem Statement
Choose the smallest useful way to give admins and developers one short git-style command for common repo tasks without replacing the project's existing Python entrypoints or adding extra toolchain requirements.

### Option A: Add a repo-root shell wrapper that delegates to a Python task runner
- Pros:
  - Matches the `~/penelope/` pattern directly: short command up front, Python logic behind it.
  - Keeps help text, validation, and subcommand routing in one place while preserving a git-style UX.
  - Can wrap the current local server, test, and operator commands instead of inventing new execution paths.
  - Easy to extend later with admin helpers such as env sync or record maintenance.
- Cons:
  - Requires maintaining both a small shell wrapper and a Python command module.
  - POSIX wrapper behavior needs a little care around virtualenv guidance and shell compatibility.

### Option B: Add a Python-only command entrypoint
- Pros:
  - Single-language implementation with no shell wrapper to maintain.
  - Easier to test directly from Python.
  - Avoids shell portability concerns.
- Cons:
  - Invocation stays longer and less git-like (`python3 ...` or `python -m ...`).
  - Lower discoverability for admins and contributors who just want one obvious repo command.
  - More friction to make it the documented default workflow.

### Option C: Add a Makefile or Justfile with aliases
- Pros:
  - Quick to wire up for common developer tasks.
  - Familiar to many contributors.
  - Keeps individual commands very small.
- Cons:
  - Adds a separate tool convention rather than following the Penelope pattern.
  - Weaker fit for admin/operator workflows and weaker built-in help and argument validation.
  - `make` or `just` is not as universal or git-style as a dedicated repo command.

## Recommendation
Recommend Option A: add a short repo-root wrapper backed by a Python task runner.

This is the closest fit to the proven `~/penelope/` design and the cleanest way to give this repo one canonical command surface. It keeps the UX short, keeps the behavior centralized in Python, and lets the project standardize common tasks without turning each task into a separate script or external-tool convention.
