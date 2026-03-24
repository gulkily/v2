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
