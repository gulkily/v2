## Stage 1 - Add explicit stale-index recovery classification
- Changes:
  - Extended `forum_core/post_index.py` readiness metadata with an explicit schema-compatibility metadata key and resolved recovery classification so stale states can distinguish `current`, `incremental_catch_up`, and `full_rebuild`.
  - Preserved the existing `requires_rebuild` surface for callers while adding explicit `requires_full_rebuild`, `resolved_recovery_kind`, and `resolved_recovery_reason` signals for later stages and diagnostics.
  - Updated rebuild and incremental-refresh metadata writes so the index now stores both schema version and schema compatibility version.
- Verification:
  - `python -m unittest tests.test_post_index.PostIndexSchemaTests.test_post_index_readiness_reports_current_index_without_rebuild tests.test_post_index.PostIndexSchemaTests.test_post_index_readiness_reports_stale_index_when_head_drifts tests.test_post_index.PostIndexSchemaTests.test_post_index_readiness_requires_full_rebuild_when_schema_compatibility_metadata_is_missing`
- Notes:
  - Stage 1 does not change recovery execution yet; `ensure_post_index_current(...)` still runs the existing rebuild path after classifying the stale state.

## Stage 2 - Fast-forward compatible head drift through incremental catch-up
- Changes:
  - Added commit-range and per-commit touched-path helpers in `forum_core/post_index.py` so compatible head drift can be replayed through the existing `refresh_post_index_after_commit(...)` path.
  - Updated `ensure_post_index_current(...)` to attempt incremental catch-up when readiness resolves to `incremental_catch_up`, then fall back to the existing full rebuild path when the commit range is unsafe or unsupported.
  - Kept incremental catch-up intentionally narrow: commits touching `records/identity-links/`, unsupported change statuses, or unsafe history shapes fall back to full rebuild instead of forcing broader refresh semantics.
- Verification:
  - `python -m unittest tests.test_post_index.PostIndexBuildTests.test_ensure_post_index_current_fast_forwards_head_drift_without_full_rebuild tests.test_post_index.PostIndexBuildTests.test_ensure_post_index_current_falls_back_to_full_rebuild_for_deleted_post_commit`
  - Manual smoke check with a disposable repo and an empty follow-up commit confirmed `ensure_post_index_current(...)` advanced `indexed_head` to the new `HEAD` without a full rebuild path.
- Notes:
  - This stage reduces rebuild frequency only for safe, replayable head drift. Unsupported history patterns still intentionally use the canonical full rebuild contract.

## Stage 3 - Add regression coverage and recovery-path diagnostics
- Changes:
  - Added regression coverage in `tests/test_post_index.py` for both compatible head-drift catch-up and unsupported deleted-post fallback rebuilds.
  - Added background-operation coverage in `tests/test_background_operation_events.py` that the direct incremental catch-up helper records a distinct maintenance operation name in the existing operation-events surface.
  - Kept existing startup and refresh-page request tests passing with the new readiness metadata so the covered UI flows still behave correctly while operator diagnostics now include explicit recovery kind and reason fields.
- Verification:
  - `python -m unittest tests.test_post_index.PostIndexSchemaTests.test_post_index_readiness_reports_current_index_without_rebuild tests.test_post_index.PostIndexSchemaTests.test_post_index_readiness_reports_stale_index_when_head_drifts tests.test_post_index.PostIndexSchemaTests.test_post_index_readiness_requires_full_rebuild_when_schema_compatibility_metadata_is_missing tests.test_post_index.PostIndexBuildTests.test_ensure_post_index_current_fast_forwards_head_drift_without_full_rebuild tests.test_post_index.PostIndexBuildTests.test_ensure_post_index_current_falls_back_to_full_rebuild_for_deleted_post_commit tests.test_background_operation_events.BackgroundOperationEventsTests.test_incremental_catch_up_records_distinct_background_operation tests.test_post_index_startup`
- Notes:
  - Nested `tracked_operation(...)` calls are intentionally suppressed, so the distinct catch-up operation is verified on the direct helper path while ordinary `ensure_post_index_current(...)` still records the outer startup operation plus explicit recovery-kind diagnostics in logs.
