## Stage 1 - Add one shared operation-timing recorder and recent-event store
- Changes:
  - Added `forum_core.operation_events` as the shared operation lifecycle seam for starting, updating, completing, and failing recent operation records.
  - Added a separate local SQLite-backed recent-event store at `state/cache/operation_events.sqlite3` with short-retention cleanup for completed operations.
  - Added focused persistence tests covering operation lifecycle, failed operations, and retention pruning.
- Verification:
  - `python -m unittest tests.test_operation_events`
- Notes:
  - The store is intentionally small and local. Later stages will attach HTTP requests, non-request tasks, and the operator-facing report to this same seam.
