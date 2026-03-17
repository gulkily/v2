## Stage 1 - Add merged activity event helpers
- Changes:
  - Added a shared `ActivityEvent` model plus fixed filter parsing and mixed reverse-chronological sorting in `forum_web/web.py`.
  - Added `load_activity_events(...)` so git-driven content activity and moderation records can be combined into one timeline before any route/template changes.
  - Extended `tests/test_site_activity_git_log_helpers.py` to cover filter parsing, mixed ordering, and kind-specific filtering.
- Verification:
  - Ran `python -m unittest tests.test_site_activity_git_log_helpers`
  - Ran `python -m unittest tests.test_site_activity_page`
- Notes:
  - This stage only establishes the merged read model. `/activity/` still renders the old content-only page until Stage 2.
