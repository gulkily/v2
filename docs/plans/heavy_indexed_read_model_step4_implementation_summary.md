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
