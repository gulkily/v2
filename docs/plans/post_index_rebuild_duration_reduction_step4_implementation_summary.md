## Stage 1 - Add detailed timing visibility for full rebuild timestamp work
- Changes:
  - Extended full rebuild timestamp collection in `forum_core/post_index.py` to report two substeps: post-path enumeration and git-log scanning.
  - Routed full rebuild and incremental path-specific timestamp lookups through one shared per-path helper so later optimization can reuse the same seam.
  - Added regression coverage that confirms `post_index_rebuild` operation events include the new timestamp substeps.
- Verification:
  - `python -m unittest tests.test_background_operation_events`
  - `python -m unittest tests.test_post_index` currently fails in an unrelated existing test fixture: `tests.test_post_index.PostIndexBuildTests.test_rebuild_post_index_caches_identity_members_username_claims_and_roots` raises `TypeError: MergeRequestState.__init__() missing 1 required positional argument: 'revoked'`.
- Notes:
  - The canonical rebuild timing surface still includes the existing aggregate `post_index_commit_timestamps` phase; the new substeps make that aggregate diagnosable without changing request or rebuild behavior.

## Stage 2 - Parallelize full rebuild timestamp lookups without changing timestamp semantics
- Changes:
  - Updated `post_commit_timestamps(...)` to fan out full-rebuild per-path `git log --follow` lookups with a bounded worker count instead of scanning all post histories serially.
  - Kept the existing per-path history derivation helper as the source of truth so full rebuilds and incremental refreshes still share the same timestamp semantics.
  - Added focused regression coverage that confirms full rebuild timestamp collection goes through the shared per-path helper and that rebuild timing still exposes the expected phases.
- Verification:
  - `python -m unittest tests.test_background_operation_events tests.test_post_index.PostIndexBuildTests.test_rebuild_post_index_stores_commit_derived_timestamps tests.test_post_index.PostIndexBuildTests.test_post_commit_timestamps_uses_shared_per_path_helper_for_full_rebuild tests.test_post_index.PostIndexBuildTests.test_incremental_refresh_uses_touched_path_timestamps_only`
  - Manual smoke check with a disposable git repo and `rebuild_post_index(..., timing_callback=...)` confirmed the rebuild still reports `post_index_commit_timestamp_paths`, `post_index_commit_timestamp_git_logs`, `post_index_commit_timestamps`, `post_index_upsert_all_posts`, and `post_index_commit_sqlite`.
- Notes:
  - This stage intentionally optimizes only the legitimate full rebuild path; rebuild-triggering policy and stale-index recovery strategy remain unchanged.
