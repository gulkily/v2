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

## Stage 4 - Add PHP-native profile reads
- Changes:
  - Extended PHP-native read artifacts to build and store `/profiles/<identity-slug>` snapshots in the shared SQLite snapshot store.
  - Added PHP-host native route handling for queryless public profile pages and aligned profile cookie-safety rules with the existing public-read contract.
  - Kept the expansion bounded to `/profiles/...` and left `/user/...`, merge, update, and request-shaped profile routes on the existing dynamic path.
  - Added focused snapshot and PHP-host tests covering profile snapshot generation, profile native hits with `forum_identity_hint`, and fallback when unexpected cookies are present.
- Verification:
  - Ran `python3 -m pytest -q tests/test_php_native_reads.py tests/test_php_host_cache.py tests/test_post_index_startup.py`.
  - Result: `41 passed in 15.03s`.
- Notes:
  - CGI rebuild requests still need the real startup rebuild path, so Stage 2 was narrowed to skip eager startup only for non-rebuild CGI reads.

## Stage 5 - Add deploy verification checklist
- Changes:
  - Added an operator checklist for post-deploy warmup, response-source verification, slow-path diagnosis, and freshness checks across `/`, `/threads/...`, and `/profiles/...`.
  - Linked that checklist from the canonical PHP-host operator section in `docs/developer_commands.md`.
- Verification:
  - Reviewed the checklist against the current response headers and route set added through Stages 1-4.
  - Confirmed the linked doc path resolves from `docs/developer_commands.md`.
- Notes:
  - Stage 5 is documentation/operator guidance only; no runtime behavior changed in this stage.
