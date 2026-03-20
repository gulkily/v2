## Stage 1 - Add post-index readiness assessment
- Changes:
  - Added a reusable `PostIndexReadiness` model and `post_index_readiness(repo_root)` helper in `forum_core/post_index.py`.
  - Refactored `ensure_post_index_current(...)` to reuse the same readiness calculation before deciding whether a rebuild is required.
  - Added focused readiness tests for current and stale index states in `tests/test_post_index.py`.
- Verification:
  - `python -m unittest tests.test_post_index.PostIndexSchemaTests`
- Notes:
  - The readiness seam is intentionally read-only so the web layer can preflight stale-index routes before choosing how to respond.

## Stage 2 - Show a reindex wait page on covered routes
- Changes:
  - Added covered-route preflight logic in `forum_web/web.py` for `/`, `/threads/...`, `/profiles/...`, and `/user/...`.
  - Added a one-at-a-time background rebuild launcher so stale index requests can return an immediate wait page instead of blocking on a full rebuild.
  - Added a shared “Refreshing forum data” page with automatic retry and a link to recent slow operations.
  - Added request-level tests covering startup-time and post-startup stale-index waits.
- Verification:
  - `python -m unittest tests.test_post_index_startup tests.test_post_index.PostIndexSchemaTests`
- Notes:
  - The first slice intentionally keeps the feedback generic and page-level; it does not attempt step-by-step progress reporting inside the rebuild.
