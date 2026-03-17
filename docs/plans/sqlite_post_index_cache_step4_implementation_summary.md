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

## Stage 3 - Refresh the index after successful repo writes
- Changes:
  - Added `ensure_post_index_current(...)`, `refresh_post_index_after_commit(...)`, and indexed-root lookup helpers to `forum_core/post_index.py` so the derived database can stay current during normal operation and repair itself when metadata says it is stale.
  - Hooked `forum_cgi/posting.py:commit_post(...)` into the shared post-index refresh path so successful commit-backed repo writes update the derived cache immediately.
  - Extended `tests/test_post_index.py` with write-through coverage for stored thread creation and a commit-backed task-status update.
- Verification:
  - Ran `python -m unittest tests.test_post_index`
  - Ran `python -m unittest tests.test_task_thread_pages tests.test_board_index_page`
- Notes:
  - Stage 3 keeps the SQLite layer current for normal commit-backed writes, but no read surface uses it for ordering until Stage 4.

## Stage 4 - Use the index for homepage ordering
- Changes:
  - Updated `forum_web/web.py` so `visible_threads(...)` can sort root threads with SQLite-derived `updated_at` and `created_at` timestamps when a repo root is available, while preserving the existing pinned-first rule and falling back safely when the index has no useful timestamp data.
  - Switched the board index and API list-index routes onto the index-aware `visible_threads(...)` call path.
  - Extended `tests/test_board_index_page.py` with a git-backed recency-ordering case that proves the homepage stops relying on raw `post_id` order once the derived index is available.
- Verification:
  - Ran `python -m unittest tests.test_board_index_page tests.test_post_index`
  - Ran `python -m unittest tests.test_task_thread_pages tests.test_site_activity_page tests.test_instance_info_page`
- Notes:
  - The first read-surface migration is intentionally narrow: the homepage and shared list-index ordering now use the derived timestamps, while the broader thread/post rendering model still comes from canonical parsed files.
