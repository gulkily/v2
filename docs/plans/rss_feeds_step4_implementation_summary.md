## Stage 1 - Add shared RSS feed helpers
- Changes:
  - Added shared RSS feed primitives in `forum_web/web.py`, including `FeedItem`, pubDate formatting helpers, XML rendering, and scope-specific feed-item loaders for activity, board scope, and thread scope.
  - Extended `tests/test_site_activity_git_log_helpers.py` with focused coverage for RSS XML output and feed-item loading across content, moderation, code, board, and thread contexts.
- Verification:
  - `python -m pytest tests/test_site_activity_git_log_helpers.py`
- Notes:
  - This stage only shapes feed data and XML; no HTTP routes or HTML discovery links are exposed yet.

## Stage 2 - Expose RSS routes for approved scopes
- Changes:
  - Extended the `/`, `/activity/`, and `/threads/{thread-id}` read routes to return RSS when `format=rss` is requested, while keeping the existing HTML responses intact.
  - Added query-parameter board scope for RSS on `/` via `board_tag=...`, and reused the same board filtering in the HTML board index renderer so the board-scoped feed URL has a matching page scope.
  - Skipped post-index reindex feedback wrappers for RSS requests so feed clients receive XML directly instead of the HTML refresh shell.
  - Added route-level RSS coverage to the activity, board index, and thread page tests.
- Verification:
  - `python -m pytest tests/test_site_activity_page.py tests/test_board_index_page.py tests/test_task_thread_pages.py`
- Notes:
  - RSS is currently exposed through query-parameter negotiation (`format=rss`) rather than separate feed-only endpoints.

## Stage 3 - Add RSS discovery to HTML pages
- Changes:
  - Extended the shared page shell to support head-level feed discovery markup and added `<link rel="alternate" type="application/rss+xml">` metadata for the board index, activity page, and thread pages.
  - Added one visible `RSS feed` chip to those same HTML pages so the subscription URL is discoverable without inspecting source.
  - Added HTML assertions in the page test suites to verify both the visible discovery link and the alternate-feed metadata.
- Verification:
  - `python -m pytest tests/test_site_activity_page.py tests/test_board_index_page.py tests/test_task_thread_pages.py`
- Notes:
  - Board-filtered HTML pages now advertise the board-filtered RSS URL when `board_tag` scope is active.

## Stage 4 - Lock RSS behavior into regression coverage
- Changes:
  - Added focused edge-case coverage for filtered activity RSS output, unknown board-tag RSS requests, and missing-thread RSS requests.
  - Re-ran the combined RSS-related helper and page suites so the final stage validates helper shaping, route responses, discovery markup, and error handling together.
- Verification:
  - `python -m pytest tests/test_site_activity_git_log_helpers.py tests/test_site_activity_page.py tests/test_board_index_page.py tests/test_task_thread_pages.py`
- Notes:
  - Missing-thread RSS requests currently fall back to the existing 404 HTML page, which keeps error handling consistent with the normal thread route.
