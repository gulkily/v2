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

## Stage 2 - Reduce synchronous refresh cost for the common new-thread write path
- Changes:
  - Narrowed the incremental post-index refresh path so it derives commit timestamps only for the touched post paths instead of rescanning git history for every post in the repository after each successful write.
  - Added focused regression coverage that proves the incremental refresh path uses the touched-path timestamp helper and still writes the expected timestamp data into the SQLite index.
- Verification:
  - Ran `python3 -m unittest tests.test_post_index.PostIndexBuildTests.test_incremental_refresh_uses_touched_path_timestamps_only`.
  - Ran `python3 -m unittest tests.test_post_index.PostIndexBuildTests.test_store_post_refreshes_index_after_successful_commit`.
  - Ran `python3 -m unittest tests.test_thread_auto_reply.ThreadAutoReplyTests.test_api_create_thread_reports_disabled_when_feature_flag_is_off`.
- Notes:
  - This stage preserves the current immediate read-after-write behavior and limits the optimization to the existing incremental refresh path for committed writes.

## Stage 3 - Add focused regression coverage for latency-sensitive create-thread behavior
- Changes:
  - Added a WSGI-level regression test that creates a thread through `/api/create_thread` and immediately verifies the new thread is visible on both its thread page and the board index.
  - Re-ran the timing-log and incremental-refresh coverage so the optimized path stays tied to observable phase data and the narrowed timestamp refresh contract.
- Verification:
  - Ran `python3 -m unittest tests.test_thread_auto_reply.ThreadAutoReplyTests.test_create_thread_is_immediately_visible_on_thread_and_board_reads`.
  - Ran `python3 -m unittest tests.test_thread_auto_reply.ThreadAutoReplyTests.test_api_create_thread_reports_disabled_when_feature_flag_is_off`.
  - Ran `python3 -m unittest tests.test_post_index.PostIndexBuildTests.test_incremental_refresh_uses_touched_path_timestamps_only`.
- Notes:
  - Coverage stays focused on correctness and immediate visibility rather than asserting brittle absolute latency thresholds.
