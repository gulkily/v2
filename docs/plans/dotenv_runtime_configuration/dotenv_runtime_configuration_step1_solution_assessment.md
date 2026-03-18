## Problem Statement
Choose the smallest useful way to let admins set existing runtime variables such as `FORUM_MODERATOR_FINGERPRINTS` through a repo-root `.env` file without fragmenting configuration across entrypoints and the new `./forum` runner.

### Option A: Add repo-root `.env` and `.env.example` support with a shared startup loader plus `./forum`-based sync workflow
- Pros:
  - Matches the `~/penelope/docs/env_setup.md` pattern directly.
  - Gives one documented place for `FORUM_MODERATOR_FINGERPRINTS`, `FORUM_REPO_ROOT`, `FORUM_HOST`, and `FORUM_PORT`.
  - Keeps the WSGI app, CGI-style commands, local scripts, and `./forum` runner aligned if they all call the same loader at process startup.
  - Gives the project one explicit operator command surface for syncing `.env` from `.env.example` instead of leaving that behavior scattered.
- Cons:
  - Adds a small startup dependency and requires touching multiple entrypoints.
  - Needs clear precedence rules between real environment variables and `.env` values.

### Option B: Keep environment-only config and document shell sourcing of `.env`
- Pros:
  - Minimal code change.
  - No new Python dependency or loader code.
  - Fits traditional CGI and server process deployment.
- Cons:
  - Does not give the project first-class `.env` support.
  - Leaves local scripts and deployed processes easy to misconfigure differently.
  - Provides no canonical `.env.example` workflow for new admins or developers using `./forum`.

### Option C: Implement a custom stdlib `.env` parser inside this repo
- Pros:
  - Avoids adding an external dependency.
  - Keeps `.env` behavior fully local to the project.
- Cons:
  - Reimplements a solved problem and diverges from the Penelope pattern.
  - Risks edge-case bugs around quoting, comments, and override behavior.
  - Makes future reuse across projects less consistent.

## Recommendation
Recommend Option A: add repo-root `.env` and `.env.example` support with one shared startup loader and an explicit `./forum` sync workflow.

This is the smallest coherent adaptation of the Penelope pattern. It gives admins a real `.env` workflow, keeps existing environment-variable behavior intact, and avoids inventing a second configuration mechanism. The next steps should stay narrow: load `.env` once near startup, document the currently supported forum variables, expose missing-key sync through `./forum`, and keep direct environment overrides working for deployment environments that already set them externally.
