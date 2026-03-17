## Stage 1 - Add SQLite index and schema layer
- Changes:
  - Added `forum_core/post_index.py` with a stable derived-database path under `state/cache/`, a focused `open_post_index(...)` entrypoint, and idempotent schema setup around the initial normalized post/cache tables.
  - Added schema-version handling via SQLite `user_version` and explicit missing-column upgrades so older databases can be reopened without manual migration steps.
  - Added `state/cache/` to `.gitignore` so the derived database location is not tracked with source files.
  - Added `tests/test_post_index.py` covering first-open creation, repeated open idempotence, and upgrade from an older `posts` table shape.
- Verification:
  - Ran `python -m unittest tests.test_post_index tests.test_board_index_page tests.test_task_thread_pages`
- Notes:
  - This stage establishes only the SQLite/migration layer. The index is not populated from canonical records yet, and no read or write paths use it until later stages.
