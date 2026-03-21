## Stage 1 - Add explicit stale-index recovery classification
- Changes:
  - Extended `forum_core/post_index.py` readiness metadata with an explicit schema-compatibility metadata key and resolved recovery classification so stale states can distinguish `current`, `incremental_catch_up`, and `full_rebuild`.
  - Preserved the existing `requires_rebuild` surface for callers while adding explicit `requires_full_rebuild`, `resolved_recovery_kind`, and `resolved_recovery_reason` signals for later stages and diagnostics.
  - Updated rebuild and incremental-refresh metadata writes so the index now stores both schema version and schema compatibility version.
- Verification:
  - `python -m unittest tests.test_post_index.PostIndexSchemaTests.test_post_index_readiness_reports_current_index_without_rebuild tests.test_post_index.PostIndexSchemaTests.test_post_index_readiness_reports_stale_index_when_head_drifts tests.test_post_index.PostIndexSchemaTests.test_post_index_readiness_requires_full_rebuild_when_schema_compatibility_metadata_is_missing`
- Notes:
  - Stage 1 does not change recovery execution yet; `ensure_post_index_current(...)` still runs the existing rebuild path after classifying the stale state.
