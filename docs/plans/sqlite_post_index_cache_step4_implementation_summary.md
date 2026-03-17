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

## Stage 2 - Rebuild the index from canonical records and git history
- Changes:
  - Extended `forum_core/post_index.py` with full index rebuild support, normalized row upserts, metadata storage, and git-history timestamp derivation for `created_at` and `updated_at`.
  - Added rebuild coverage in `tests/test_post_index.py` for commit-derived timestamps and normalized child-table population for board tags, task dependencies, and task sources.
- Verification:
  - Ran `python -m unittest tests.test_post_index`
  - Ran `python -m unittest tests.test_board_index_page tests.test_task_thread_pages`
- Notes:
  - The rebuild path now establishes the full derived model, but normal app writes still do not refresh the index automatically until Stage 3.
