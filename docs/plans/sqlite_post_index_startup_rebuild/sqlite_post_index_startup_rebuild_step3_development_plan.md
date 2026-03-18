## Stage 1
- Goal: tighten the SQLite index readiness contract so schema-version changes and missing backfills require a full rebuild.
- Dependencies: approved Step 2; current `forum_core/post_index.py` readiness path; existing schema-version and index-metadata logic.
- Expected changes: extend `ensure_post_index_current(...)` and related readiness helpers so the app detects when the current schema version has not been fully rebuilt, rather than only checking row count and `indexed_head`; planned contracts such as explicit schema-version readiness metadata or equivalent deterministic checks, and rebuild triggers tied to `POST_INDEX_SCHEMA_VERSION`; no new storage source.
- Verification approach: open older or partially upgraded indexes in tests and confirm the readiness path rebuilds them instead of leaving new derived tables empty.
- Risks or open questions:
  - choosing the smallest deterministic backfill-readiness signal that does not require per-feature heuristics forever
  - avoiding rebuild loops when readiness metadata is updated during rebuild itself
- Canonical components/API contracts touched: `ensure_post_index_current(...)`; schema-version handling; index metadata readiness contract.

## Stage 2
- Goal: run the index readiness check eagerly during server startup while preserving the existing lazy fallback on indexed use.
- Dependencies: Stage 1; current server startup path; existing lazy indexed-read calls into the post index.
- Expected changes: add one startup-time call into the post-index readiness path so the app rebuilds the index before serving normal traffic when needed, while keeping lazy `ensure_post_index_current(...)` calls in indexed read helpers for fallback correctness; planned contracts such as one startup initialization hook and the unchanged lazy read-side readiness entrypoint.
- Verification approach: start the app against a stale or schema-behind index and confirm startup triggers a rebuild; then request an indexed read and confirm the lazy fallback still works if startup did not already make the index current.
- Risks or open questions:
  - choosing the narrowest startup hook that runs reliably across the current server launch modes
  - avoiding duplicate rebuild work if startup and first indexed use happen close together
- Canonical components/API contracts touched: server startup initialization; post-index readiness entrypoint; indexed read fallback behavior.

## Stage 3
- Goal: lock the startup-rebuild behavior into focused regression coverage and any minimal operator-facing diagnostics.
- Dependencies: Stages 1-2; current post-index tests; any existing startup or integration-style tests that can cover initialization behavior.
- Expected changes: add focused tests for schema-upgrade-triggered rebuilds, startup-triggered readiness checks, and lazy fallback after startup; add small metadata or logging assertions if needed so rebuild cause is inspectable; planned contracts such as test fixtures for stale indexes and schema-behind databases.
- Verification approach: run targeted unittest coverage for readiness detection, eager startup rebuild, and lazy fallback behavior; confirm the observed author-table-empty failure mode is prevented.
- Risks or open questions:
  - keeping startup-behavior tests stable without overcoupling them to the exact server boot sequence
  - deciding how much diagnostic metadata is useful without turning this into a larger observability feature
- Canonical components/API contracts touched: post-index readiness tests; startup initialization coverage; any minimal rebuild-cause metadata or logging.
