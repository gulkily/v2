## Stage 1 - Indexed post and thread read contracts
- Changes:
  - Added `load_indexed_posts(...)` and `load_indexed_threads(...)` in [forum_core/post_index.py](/home/wsl/v2/forum_core/post_index.py) so hot read paths can reconstruct canonical `Post` and `Thread` objects from `post_index.sqlite3` instead of reparsing text records.
  - Reused existing indexed task, tag, author, and signing fields so the new loaders preserve current read-shape expectations for downstream renderers.
  - Added focused round-trip tests in [test_post_index.py](/home/wsl/v2/tests/test_post_index.py) covering task metadata, signing fields, and thread grouping from the indexed store.
- Verification:
  - Ran `python -m unittest tests.test_post_index.PostIndexBuildTests.test_load_indexed_posts_reconstructs_posts_with_task_metadata_and_signing_fields tests.test_post_index.PostIndexBuildTests.test_load_indexed_threads_groups_indexed_posts_without_raw_record_parsing`
  - Result: `OK`
- Notes:
  - The indexed contract currently normalizes task-source ordering by indexed row order; callers should treat that ordering as index-defined rather than source-text-preserved.

## Stage 2 - Move board reads onto indexed posts
- Changes:
  - Updated the board-index route in [web.py](/home/wsl/v2/forum_web/web.py) to load posts, threads, and board tags from the indexed SQLite read path instead of `load_repository_state()`.
  - Kept moderation and title-update behavior on their existing authoritative paths so rendered board behavior stays unchanged while the hot route stops reparsing post records.
  - Added a board-page regression in [test_board_index_page.py](/home/wsl/v2/tests/test_board_index_page.py) proving `/` still renders when raw `load_posts(...)` is unavailable.
- Verification:
  - Ran `python -m unittest tests.test_board_index_page.BoardIndexPageTests.test_board_index_uses_indexed_posts_without_raw_record_parsing tests.test_board_index_page.BoardIndexPageTests.test_board_index_preserves_key_destination_links`
  - Result: `OK`
- Notes:
  - This stage only moved the board page itself; board-adjacent feeds and non-hot routes still use the older dynamic path.

## Stage 3 - Move thread and post reads onto indexed posts
- Changes:
  - Updated thread and post read routes in [web.py](/home/wsl/v2/forum_web/web.py) to load post/thread data from the indexed SQLite path instead of reparsing canonical post files.
  - Passed indexed post collections through shared render helpers so thread and post rendering no longer fall back to raw `load_posts(...)` during card/profile-link generation.
  - Added focused regressions in [test_task_thread_pages.py](/home/wsl/v2/tests/test_task_thread_pages.py) proving thread and permalink pages still render when `forum_web.web.load_posts` is patched to fail.
- Verification:
  - Ran `python -m unittest tests.test_task_thread_pages.TaskThreadPagesTests.test_task_thread_page_uses_indexed_posts_without_raw_record_parsing tests.test_task_thread_pages.TaskThreadPagesTests.test_post_permalink_page_uses_indexed_posts_without_raw_record_parsing tests.test_task_thread_pages.TaskThreadPagesTests.test_task_thread_page_renders_structured_metadata tests.test_task_thread_pages.TaskThreadPagesTests.test_post_permalink_page_uses_same_compact_metadata`
  - Result: `OK`
- Notes:
  - This stage keeps moderation and title-update records on their current authoritative paths; only post/thread materialization moved to the index.
