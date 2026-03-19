## Problem
The repo’s canonical command surface is `./forum`, but a clean shell account can hit missing-package failures before that command can help the operator recover. The next slice should make first-run setup flow through `./forum` while still allowing either user-profile/global installs or a repo-local `.venv`.

## User Stories
- As an operator, I want `./forum` to remain usable as my first command on a fresh account so that the repo can guide me through missing Python setup instead of crashing immediately.
- As an operator, I want to choose either a user-profile/global install path or a repo-local `.venv` path so that I can match the hosting model I prefer.
- As a maintainer, I want one canonical bootstrap path documented through the existing command surface so that setup guidance does not fragment across ad hoc shell instructions.

## Core Requirements
- The feature must add one explicit first-run bootstrap/install path to `./forum` for environments where required Python packages are not installed yet.
- The bootstrap path must support both install shapes: user-profile/global Python packages and repo-local `.venv`.
- The bootstrap path must keep normal runtime commands dependent on the real installed requirements rather than silently degrading core runtime behavior.
- The feature must preserve `./forum` as the canonical operator-facing command surface rather than replacing it with a separate installer workflow.
- The repo’s setup documentation must describe the canonical bootstrap flow and the two supported install modes consistently.

## Shared Component Inventory
- `./forum`: reuse and extend this canonical command wrapper as the primary operator-facing bootstrap surface.
- `python3 scripts/forum_tasks.py ...`: reuse this direct task-runner surface and keep its high-level command behavior aligned with `./forum` rather than introducing a separate contract.
- Local setup docs in `README.md`: extend the existing setup guidance rather than adding a second onboarding document.
- Operator command reference in `docs/developer_commands.md`: extend the existing command reference so bootstrap/install guidance stays in the canonical command doc.

## Simple User Flow
1. An operator clones the repo on a clean account.
2. They run `./forum` using the documented bootstrap command.
3. The command guides them through installing the required Python packages using either their chosen user-profile/global path or a repo-local `.venv`.
4. After installation, they continue with the normal documented setup flow and run other `./forum` commands successfully.

## Success Criteria
- A fresh-account operator can start with `./forum` instead of needing prior manual Python package setup knowledge.
- The documented bootstrap flow explicitly supports both user-profile/global installs and repo-local `.venv`.
- The canonical setup guidance in `README.md` and `docs/developer_commands.md` stays aligned with the `./forum` command surface.
- Normal runtime commands still assume the real dependencies are installed and do not silently switch to a degraded runtime mode.
