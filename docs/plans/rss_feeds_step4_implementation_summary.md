## Stage 1 - Add shared RSS feed helpers
- Changes:
  - Added shared RSS feed primitives in `forum_web/web.py`, including `FeedItem`, pubDate formatting helpers, XML rendering, and scope-specific feed-item loaders for activity, board scope, and thread scope.
  - Extended `tests/test_site_activity_git_log_helpers.py` with focused coverage for RSS XML output and feed-item loading across content, moderation, code, board, and thread contexts.
- Verification:
  - `python -m pytest tests/test_site_activity_git_log_helpers.py`
- Notes:
  - This stage only shapes feed data and XML; no HTTP routes or HTML discovery links are exposed yet.
