## Stage 1 - Tighten index readiness detection
- Changes:
  - Updated `forum_core/post_index.py` so schema-version backfill is tracked explicitly through `indexed_schema_version` metadata.
  - Extended `ensure_post_index_current(...)` to require a full rebuild when schema-version metadata is missing or stale, instead of trusting only `indexed_head` and post count.
  - Expanded `tests/test_post_index.py` with a schema-backfill regression that simulates a partially upgraded index and confirms the readiness path rebuilds it.
- Verification:
  - Ran `python -m unittest tests.test_post_index`
- Notes:
  - This stage changes only the readiness contract. The eager startup hook itself is added in Stage 2.
