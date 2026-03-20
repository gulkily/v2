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

## Stage 3 - Lock the route behavior into regression coverage
- Changes:
  - Added a retry-link regression test to ensure the wait page preserves the original query string.
  - Tightened the wait-page preflight so it only activates for existing stale git-backed index state, not cold-start index creation.
  - Switched the background worker to run a direct rebuild and log failures so request tests do not leave noisy uncaught thread errors behind.
  - Replaced the wait page with a self-contained HTML response that uses inline styling and inline retry logic instead of depending on the shared CSS and JS asset pipeline.
- Verification:
  - `python -m unittest tests.test_post_index_startup tests.test_post_index.PostIndexSchemaTests tests.test_board_index_page tests.test_username_profile_route`
- Notes:
  - A broader run including `tests.test_profile_update_page` still reports two existing username-update-link expectation failures in profile rendering, which are outside the files changed for this feature.
