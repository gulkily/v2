## Stage 1 - Align native read cookie safety
- Changes:
  - Updated PHP-native board and thread route guards to reuse the shared cache-busting credential policy instead of rejecting every cookie unconditionally.
  - Expanded the shared identity-hint cache-safe path contract so `/threads/...` requests with only `forum_identity_hint` remain eligible for public fast paths.
  - Added PHP host tests covering board and thread native reads with identity-hint cookies and unexpected-cookie fallback behavior.
- Verification:
  - Ran `python3 -m pytest -q tests/test_php_host_cache.py`.
  - Result: `21 passed in 12.83s`.
- Notes:
  - The thread case required widening the shared cookie-safety helper, not just the native route guards, because the helper previously marked all thread routes as cache-busting when any cookie was present.

## Stage 2 - Skip eager startup work for CGI reads
- Changes:
  - Added an explicit `request_runs_once(...)` helper in the Python request path.
  - Limited eager post-index startup initialization to reusable request environments, so true CGI requests no longer pay startup-style index work before route dispatch.
  - Extended startup tests to confirm CGI rebuild flows still work while non-reindex CGI routes skip eager startup initialization.
- Verification:
  - Ran `python3 -m pytest -q tests/test_post_index_startup.py`.
  - Result: `10 passed in 0.80s`.
- Notes:
  - This keeps the existing eager-startup behavior for reusable workers while making the real CGI gateway (`wsgi.run_once = True`) rely on route-level, on-demand index access instead.

## Stage 3 - Add route-specific timing steps for public reads
- Changes:
  - Added reusable timed request-step recording for request-scoped operation events.
  - Instrumented board, thread, and profile read handlers with named phases for repository load, lookup/context building, and page rendering.
  - Extended request-operation tests to assert the new timing steps for `/`, `/threads/...`, and `/profiles/...`, and aligned that test file with the current string-normalized metadata behavior.
- Verification:
  - Ran `python3 -m pytest -q tests/test_request_operation_events.py`.
  - Result: `9 passed in 4.09s`.
- Notes:
  - The request-operation test fixture now prebuilds the post index so board/thread/profile requests exercise the actual render path rather than the stale-index refresh page.
