## Problem Statement
Choose the smallest coherent way to make `./forum` usable as the first command on a clean shell account where required Python packages may not be installed yet, while allowing either user-profile/global installs or a repo-local `.venv`.

### Option A: Add a dedicated bootstrap install path to `./forum` with selectable install target
- Pros:
  - Matches the requested operator experience: the repo’s own command works first even on a fresh account.
  - Keeps setup centered on one canonical entrypoint instead of raw ad hoc shell commands.
  - Supports both preferred install shapes: user-profile/global Python packages or a repo-local `.venv`.
  - Fits the existing wrapper model, which already treats `./forum` as the main task surface.
- Cons:
  - Expands the CLI surface slightly.
  - Requires care so bootstrap behavior and install-mode selection stay simple and predictable.

### Option B: Keep installation external and only improve docs
- Pros:
  - Smallest code scope.
  - Leaves dependency installation entirely to standard Python tooling.
- Cons:
  - Does not meet the stated goal that `./forum` itself should still help on a clean account.
  - Leaves first-run usability dependent on users knowing the right manual install command.

### Option C: Move bootstrap behavior into the shell wrapper instead of the Python task runner
- Pros:
  - Avoids some Python-side bootstrap logic.
  - Can act before Python task modules load.
- Cons:
  - Splits command behavior across shell and Python.
  - Makes parity with direct Python entrypoints harder to preserve.
  - Is less straightforward to test and extend than a single task-runner surface.

## Recommendation
Recommend Option A: add a dedicated bootstrap install path to `./forum` with selectable install target.

This is the smallest option that fully aligns with the request. The follow-on planning should stay narrow: define the first-run bootstrap behavior, keep normal runtime commands dependent on the real installed requirements, and support both user-profile/global installs and repo-local `.venv` without forcing either one as the only path.
