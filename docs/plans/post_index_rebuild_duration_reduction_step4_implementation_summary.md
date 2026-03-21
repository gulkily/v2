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
