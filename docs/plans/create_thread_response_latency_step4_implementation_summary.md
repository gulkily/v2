## Stage 1 - Add phase-level timing visibility to the create-thread path
- Changes:
  - Added lightweight timing callbacks through the canonical create-thread write path so the service records phase durations for parse or validation, detached-signature verification, git add, git commit, rev-parse, post-index refresh, and auto-reply handling.
  - Extended post-index instrumentation so both the rebuild path and the incremental refresh path report their internal load, timestamp, upsert, and SQLite commit subphases.
  - Added focused coverage that asserts `/api/create_thread` emits one timing log entry with the expected phase names when auto-reply is disabled.
- Verification:
  - Ran `python3 -m unittest tests.test_thread_auto_reply.ThreadAutoReplyTests.test_api_create_thread_reports_disabled_when_feature_flag_is_off`.
  - Ran `python3 -m unittest tests.test_post_index.PostIndexBuildTests.test_store_post_refreshes_index_after_successful_commit`.
- Notes:
  - The first create-thread against a repo without an existing index now reports rebuild-phase timings as part of the same create-thread timing log.
