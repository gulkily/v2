## Problem
The forum already depends on runtime environment variables such as `FORUM_MODERATOR_FINGERPRINTS`, `FORUM_REPO_ROOT`, `FORUM_HOST`, and `FORUM_PORT`, but admins and developers must set them manually for each process and existing `.env` files can drift behind newer `.env.example` entries. The project also now has a repo-level CLI runner at `./forum`, so the next slice should add the smallest useful repo-root `.env` workflow that stays consistent across runtime entrypoints and that CLI surface without adding a new admin UI, config API, or alternate configuration model.

## User Stories
- As an admin, I want to set `FORUM_MODERATOR_FINGERPRINTS` in `.env` so moderator access survives restarts without manual shell exports.
- As an admin, I want an explicit `./forum` command that updates `.env` from newer `.env.example` defaults so newly documented settings become visible without overwriting existing values.
- As a developer, I want the local server, CGI-style entrypoints, and `./forum` commands to read the same repo-root `.env` so local behavior stays consistent across commands.
- As a maintainer, I want a committed `.env.example` that documents every supported forum setting so new environments can be bootstrapped predictably.
- As a deployer, I want direct environment variables to keep working so service managers and shell-based deployments do not break.

## Core Requirements
- The slice must add repo-root `.env` loading before existing forum environment variables are read by the main local, CLI, and CGI-style startup surfaces.
- The slice must document the currently supported runtime settings in a committed `.env.example`, including at least `FORUM_MODERATOR_FINGERPRINTS`, `FORUM_REPO_ROOT`, `FORUM_HOST`, and `FORUM_PORT`.
- The slice must make `.env.example` follow the documented Penelope-style conventions: a short explanatory header, grouped variable comments, example values where helpful, and commented optional assignments so unset and blank remain distinguishable.
- The slice must add one explicit admin/developer sync command exposed through `./forum` that compares `.env.example` against `.env`, creates `.env` when missing, and appends only missing documented keys without overwriting existing values.
- The slice must keep startup read-only with respect to `.env`: launch paths and `./forum` command paths should surface a clear notice when `.env` is missing documented keys, but should not mutate `.env` implicitly.
- The slice must ensure the sync behavior is idempotent, avoids duplicate keys, and derives defaults from documented assignment lines rather than plain explanatory prose comments.
- The slice must preserve the current environment-variable names and keep explicit process environment values authoritative over `.env` values.
- The slice must keep `.env` out of version control while treating `.env.example` as the canonical documented config surface.
- The slice must treat `.env.example` as the authoritative config catalog, meaning any newly supported runtime setting is added there in the same change that introduces it.
- The slice must document that startup-loaded config changes require a process restart.
- The slice must avoid a browser admin panel, config-editing API, custom config-file format, or renaming existing settings.

## Shared Component Inventory
- Existing runtime config surfaces: reuse the current environment-backed startup behavior in the read-only WSGI app, the local run script, the new `./forum` runner, and the CGI-style write entrypoints; this feature extends startup loading and operator tooling only, not request/response contracts.
- Existing moderation authorization surface: reuse `FORUM_MODERATOR_FINGERPRINTS` as the canonical moderator allowlist input, with `.env` serving only as another source for the same value.
- Existing repository selection surface: reuse `FORUM_REPO_ROOT` for both read and write paths so repo selection stays consistent.
- Existing local server surface: reuse `FORUM_HOST` and `FORUM_PORT` for the local read-only server rather than introducing new setting names.
- Existing documentation surface: add `.env.example` as the shared documented source of truth because the repo currently has no committed env template.
- Existing admin/developer command surface: extend `./forum` as the canonical operator-facing command surface for env tooling because the repo now has a dedicated task runner.
- New UI/API surfaces: none; this slice should not add any new browser pages or HTTP routes.

## Simple User Flow
1. An admin or developer copies `.env.example` to `.env`.
2. They set `FORUM_MODERATOR_FINGERPRINTS` and any other desired forum runtime values in `.env`.
3. Later, when the repo adds new documented settings to `.env.example`, they run `./forum env-sync` to append only missing keys into `.env`.
4. They start or restart the existing local server or invoke the relevant `./forum` command.
5. The process loads `.env` during startup and the existing env-backed code paths use those values.
6. If startup or `./forum` detects `.env.example` keys missing from `.env`, it surfaces a notice pointing to `./forum env-sync` rather than silently editing `.env`.
7. If the shell or service manager provides an explicit environment variable, that explicit value continues to take precedence.

## Success Criteria
- Setting `FORUM_MODERATOR_FINGERPRINTS` in `.env` is sufficient for authorized moderation after restart without requiring a manual export in the launch shell.
- Setting `FORUM_HOST`, `FORUM_PORT`, and `FORUM_REPO_ROOT` in `.env` affects the existing startup surfaces consistently.
- Running `./forum env-sync` creates `.env` when needed and appends only missing documented keys from `.env.example` without overwriting existing values.
- Re-running `./forum env-sync` does not duplicate existing keys.
- Startup and `./forum` surfaces can detect missing documented keys and direct the operator to `./forum env-sync` without mutating `.env` automatically.
- The repo contains a documented `.env.example` and ignores the real `.env` file.
- Existing routes remain unchanged, `./forum` becomes the canonical env tool surface, and no separate config API or admin UI is introduced.
- The resulting pattern is simple enough to extend to later runtime settings without revisiting the configuration model.

## Checklist Of Patterns And Functionality To Implement
- [ ] Add a repo-root `.env.example` with comments and documented forum runtime variables.
- [ ] Format `.env.example` using the same conventions as Penelope: explanatory header, grouped comments, examples where useful, and commented optional defaults.
- [ ] Ignore the repo-root `.env` file in version control.
- [ ] Add one shared `.env` loading path used before env reads occur.
- [ ] Make the shared loader apply to the local read-only server, WSGI app startup path, the `./forum` runner, and CGI-style write entrypoints.
- [ ] Add `env-sync` to `./forum` so the repo-level CLI is the canonical way to append missing keys from `.env.example` into `.env` and create `.env` if it does not exist.
- [ ] Keep the sync behavior no-overwrite, no-duplicate, and safe against copying plain prose comments as settings.
- [ ] Add a startup and CLI missing-key notice that points operators to `./forum env-sync` instead of modifying `.env` automatically.
- [ ] Keep existing environment-variable names and preserve explicit environment override behavior.
- [ ] Treat `.env.example` as the authoritative config catalog and update it whenever a new runtime variable is introduced.
- [ ] Document restart expectations for startup-loaded settings.
- [ ] Verify `.env`-driven behavior for moderator allowlisting, repo-root selection, and local server host/port settings.
- [ ] Verify `./forum env-sync` behavior for first-time setup, later missing-key sync, and repeated idempotent runs.
