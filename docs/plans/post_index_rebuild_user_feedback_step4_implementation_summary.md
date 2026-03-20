## Stage 1 - Add post-index readiness assessment
- Changes:
  - Added a reusable `PostIndexReadiness` model and `post_index_readiness(repo_root)` helper in `forum_core/post_index.py`.
  - Refactored `ensure_post_index_current(...)` to reuse the same readiness calculation before deciding whether a rebuild is required.
  - Added focused readiness tests for current and stale index states in `tests/test_post_index.py`.
- Verification:
  - `python -m unittest tests.test_post_index.PostIndexSchemaTests`
- Notes:
  - The readiness seam is intentionally read-only so the web layer can preflight stale-index routes before choosing how to respond.
