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

## Stage 2 - Render the merged filtered activity page
- Changes:
  - Extended `/activity/` to accept fixed filter modes and render one mixed timeline with existing commit cards plus moderation cards.
  - Updated `templates/activity.html` to show filter chips and a shared event stack while preserving the repository snapshot panel.
  - Expanded `tests/test_site_activity_page.py` to cover the default merged view and the content/moderation filter modes.
- Verification:
  - Ran `python -m unittest tests.test_site_activity_page tests.test_site_activity_git_log_helpers`
  - Ran `python -m unittest tests.test_board_index_page tests.test_instance_info_page`
- Notes:
  - `/activity/` is now the merged timeline, but `/moderation/` still exists as a separate page until Stage 3.

## Stage 3 - Consolidate moderation navigation into the merged page
- Changes:
  - Redirected `/moderation/` to `/activity/?view=moderation` so the filtered activity page is now the compatibility path for moderation history.
  - Updated board-index navigation to point moderation users at the filtered merged activity view instead of the retired standalone moderation page.
  - Extended route tests to cover the redirect and the new activity-navigation target.
- Verification:
  - Ran `python -m unittest tests.test_site_activity_page tests.test_site_activity_git_log_helpers tests.test_board_index_page`
  - Ran `python -m unittest tests.test_instance_info_page tests.test_task_thread_pages`
- Notes:
  - The plain-text moderation API remains unchanged; this stage only consolidates the web UI history surfaces around `/activity/`.
