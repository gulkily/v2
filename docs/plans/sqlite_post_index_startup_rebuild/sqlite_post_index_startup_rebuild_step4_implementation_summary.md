## Stage 1 - Tighten index readiness detection
- Changes:
  - Updated `forum_core/post_index.py` so schema-version backfill is tracked explicitly through `indexed_schema_version` metadata.
  - Extended `ensure_post_index_current(...)` to require a full rebuild when schema-version metadata is missing or stale, instead of trusting only `indexed_head` and post count.
  - Expanded `tests/test_post_index.py` with a schema-backfill regression that simulates a partially upgraded index and confirms the readiness path rebuilds it.
- Verification:
  - Ran `python -m unittest tests.test_post_index`
- Notes:
  - This stage changes only the readiness contract. The eager startup hook itself is added in Stage 2.

## Stage 2 - Add eager startup initialization with lazy fallback preserved
- Changes:
  - Updated `forum_web/web.py` so the WSGI application eagerly calls the post-index readiness path once per repo root before normal request handling.
  - Added `tests/test_post_index_startup.py` to prove the eager initialization runs exactly once per repo root while the existing lazy `ensure_post_index_current(...)` fallback remains available in indexed helpers.
- Verification:
  - Ran `python -m unittest tests.test_post_index tests.test_post_index_startup`
- Notes:
  - This startup hook uses the same readiness path as indexed reads rather than inventing a separate initialization code path.

## Stage 3 - Lock stale-index rebuild behavior into regression coverage
- Changes:
  - Expanded `tests/test_post_index_startup.py` with a startup-path regression that simulates a stale schema-upgraded index and confirms request-time startup initialization rebuilds and backfills the missing schema-dependent data.
  - Kept the readiness behavior diagnosable through the explicit `indexed_schema_version` metadata written during rebuild and refresh.
- Verification:
  - Ran `python -m unittest tests.test_post_index tests.test_post_index_startup`
- Notes:
  - This stage specifically covers the observed failure mode where a new table existed after restart but historical rows had not been backfilled yet.
