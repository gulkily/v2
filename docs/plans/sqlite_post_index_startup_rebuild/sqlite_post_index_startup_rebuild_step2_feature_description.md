## Problem
The current derived SQLite post index can apply idempotent schema changes without guaranteeing that newly introduced derived tables are fully backfilled, which allows partially upgraded databases to exist after server restart. The next slice should make schema-version changes rebuild the full derived index, and should run that readiness check both eagerly at server startup and lazily on first indexed use so the app does not continue serving a half-migrated SQLite state.

## User Stories
- As an operator, I want the SQLite index to rebuild automatically after schema changes so that newly added derived data is actually present after restart.
- As an operator, I want the server to perform that readiness check at startup so the index is repaired before normal use when possible.
- As a developer, I want the same readiness check to run again on first indexed use so that the app remains correct even if startup initialization was skipped or failed.
- As a maintainer, I want the rebuild trigger to stay simple and deterministic so that schema upgrades do not leave ambiguous partial states.
- As a maintainer, I want the repository and git history to remain the source of truth while the SQLite index continues to be fully rebuildable derived state.

## Core Requirements
- The slice must treat schema-version changes as rebuild-required, not merely schema-extension-required.
- The slice must run the index readiness check eagerly during server startup.
- The slice must also run the same readiness check lazily on first indexed use.
- The slice must rebuild the full index when the current SQLite state is missing required backfilled data for the current schema version.
- The slice must preserve automatic idempotent schema setup and upgrade behavior.
- The slice must keep the repository and git history canonical, with SQLite rebuilt from those sources rather than patched manually.

## Shared Component Inventory
- Existing SQLite index readiness path: extend `ensure_post_index_current(...)` in `forum_core/post_index.py` because it already decides when the derived index must be rebuilt.
- Existing schema upgrade path: keep `ensure_post_index_schema(...)` as the place where schema creation and schema-version upgrades happen, but couple schema-version changes to rebuild decisions.
- Existing rebuild path: reuse `rebuild_post_index(...)` as the mechanism that backfills new schema-dependent data from canonical records and git history.
- Existing startup wiring: add one eager readiness call in the server startup path rather than inventing a separate maintenance command as the only repair entry point.
- Existing indexed read surfaces: preserve the lazy `ensure_post_index_current(...)` path so first indexed requests still self-heal if startup did not already do so.
- Existing metadata tracking: extend index metadata only if needed to make schema-version readiness explicit and deterministic.

## Simple User Flow
1. The server starts and runs the SQLite index readiness check.
2. If the schema is behind or the current schema version has not been fully backfilled, the app rebuilds the index from canonical records and git history.
3. A user later requests a page that depends on the index.
4. The same readiness check runs again on indexed access and confirms the index is already current, or rebuilds it if startup did not complete that work.

## Success Criteria
- Schema-version changes cause a full derived-index rebuild instead of leaving new tables empty.
- Server startup eagerly runs the SQLite index readiness check.
- Indexed reads still perform the same readiness check lazily as a fallback.
- The app does not continue serving a half-migrated SQLite index after restart.
- The rebuild contract remains fully derived from canonical records and git history.
