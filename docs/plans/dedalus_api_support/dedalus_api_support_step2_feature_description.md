## Problem
The repo already has a shared repo-root `.env` workflow, but it does not yet document or load a Dedalus Labs API key as part of the project’s canonical runtime configuration, nor does it provide a ready-to-use API path for a server-side LLM call. The next slice should let developers and operators configure Dedalus once and prove the integration through a minimal reusable API mechanism without exposing the key or introducing a second configuration model.

## User Stories
- As an operator, I want to set `DEDALUS_API_KEY` in the repo-root `.env` so that Dedalus-backed features can run without manual shell exports.
- As a developer, I want future Dedalus-backed tasks to use one shared server-side access surface so that auth and provider behavior stay consistent.
- As a developer, I want one minimal API path that can execute an LLM call through Dedalus so that the integration is usable immediately and can serve as the baseline for later AI features.
- As a maintainer, I want `DEDALUS_API_KEY` documented in `.env.example` and covered by `./forum env-sync` so new environments can be prepared predictably.
- As a security-conscious operator, I want the Dedalus key to remain server-side so browser users and public clients never need direct access to it.

## Core Requirements
- The slice must extend the existing repo-root `.env` and `.env.example` workflow to include `DEDALUS_API_KEY` rather than introducing a separate config file, admin page, or shell-only setup path.
- The slice must keep `DEDALUS_API_KEY` server-side and make Dedalus reachable only through backend-facing forum code paths.
- The slice must provide one ready-to-use API mechanism that performs a server-side Dedalus LLM call using the configured key.
- The slice must make the configured Dedalus access reusable across the project’s current execution surfaces so the minimal API mechanism and later Dedalus-backed features do not duplicate provider setup.
- The slice must keep explicit process environment values authoritative over `.env` values and preserve the current `./forum env-sync` operator workflow.
- The slice must stay scoped to baseline Dedalus availability plus one minimal LLM call path; broader task-specific prompts, end-user UI, and larger AI workflows belong to later slices.

## Shared Component Inventory
- Existing runtime config surface: reuse the repo-root `.env`, `.env.example`, and `./forum env-sync` workflow as the canonical operator path for `DEDALUS_API_KEY`.
- Existing startup/config loading surface: reuse the current shared env-loading behavior so the same configured key is available across `./forum`, local server startup, WSGI import paths, and CGI-backed commands.
- Existing browser surfaces: extend none in this slice; this feature should establish backend capability first rather than add a user-facing AI interface.
- Existing HTTP/API surfaces: extend the project’s current backend API approach with one minimal LLM-call mechanism because there is no existing Dedalus-facing API contract to reuse.
- New shared backend surface: add one canonical Dedalus access surface because the repo currently has no provider-level contract for either the baseline API call or later server-side tasks to reuse.

## Simple User Flow
1. A developer or operator runs `./forum env-sync` if their local `.env` is missing newly documented keys.
2. They set `DEDALUS_API_KEY` in the repo-root `.env`.
3. They start or restart the relevant repo process through the existing server, CGI, or `./forum` entrypoint.
4. A developer or internal forum client calls the minimal API mechanism for an LLM request.
5. The backend uses the shared server-side Dedalus access surface and returns the LLM result without exposing the key to the browser or requiring per-shell configuration.
6. Later Dedalus-backed features reuse the same backend access surface instead of reintroducing provider setup.

## Success Criteria
- `DEDALUS_API_KEY` is documented in the repo’s canonical `.env.example` and fits the existing `./forum env-sync` workflow.
- A configured repo-root `.env` is sufficient to make the Dedalus key available to current backend execution surfaces after restart.
- A developer can successfully use one ready-to-use API mechanism to trigger a real server-side Dedalus LLM call with the configured key.
- Future Dedalus-backed forum features can reuse one shared backend-facing access surface instead of each feature inventing its own auth path.
- No browser page or public client needs direct access to `DEDALUS_API_KEY`.
- The repo’s existing env precedence and operator workflow remain unchanged apart from adding documented Dedalus support.
