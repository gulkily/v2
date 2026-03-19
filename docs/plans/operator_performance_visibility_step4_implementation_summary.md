## Stage 1 - Add one shared operation-timing recorder and recent-event store
- Changes:
  - Added `forum_core.operation_events` as the shared operation lifecycle seam for starting, updating, completing, and failing recent operation records.
  - Added a separate local SQLite-backed recent-event store at `state/cache/operation_events.sqlite3` with short-retention cleanup for completed operations.
  - Added focused persistence tests covering operation lifecycle, failed operations, and retention pruning.
- Verification:
  - `python -m unittest tests.test_operation_events`
- Notes:
  - The store is intentionally small and local. Later stages will attach HTTP requests, non-request tasks, and the operator-facing report to this same seam.

## Stage 2 - Instrument HTTP requests and route write-path phase timings into shared operation records
- Changes:
  - Wrapped the WSGI application so every request now records one operation event with method and path metadata.
  - Routed existing write-path and post-index timing emissions into the shared recorder while preserving the existing log-based timing output for create-thread and profile-update flows.
  - Added focused request-operation tests covering completed GET requests and persisted phase timings for a create-thread POST request.
- Verification:
  - `python -m unittest tests.test_request_operation_events tests.test_thread_auto_reply tests.test_profile_update_submission`
- Notes:
  - The request records now capture full-request timing plus any nested phase timings already exposed by the write and post-index paths.

## Stage 3 - Instrument non-request post-index startup and rebuild entry points
- Changes:
  - Added `tracked_operation(...)` so non-request entry points can create operation records when no request context is active while reusing the current request record when one exists.
  - Wrapped `ensure_post_index_current(...)` and `rebuild_post_index(...)` so direct startup or maintenance runs now appear as shared recent operations with the same phase timings.
  - Added focused non-request operation tests and refreshed the startup-index test fixture so it matches the current identity-context and schema contracts.
- Verification:
  - `python -m unittest tests.test_background_operation_events tests.test_post_index_startup tests.test_operation_events`
- Notes:
  - This stage stays intentionally narrow: it covers the post-index readiness and rebuild paths first rather than attempting exhaustive instrumentation of every maintenance helper.
