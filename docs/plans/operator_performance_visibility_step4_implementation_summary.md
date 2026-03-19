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
