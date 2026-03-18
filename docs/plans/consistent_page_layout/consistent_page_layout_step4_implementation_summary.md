## Stage 1 - Canonical shared shell contract
- Changes:
  - Added shared `render_primary_nav`, `render_site_header`, and `render_site_footer` helpers in `forum_web/templates.py` so the canonical shell markup lives in one place.
  - Updated `render_page(...)` to use the shared helpers for its default header/footer path.
  - Switched the compose page's custom header override to the new shared header helper with intro content disabled, keeping compose on the same shell contract without duplicating markup.
- Verification:
  - Ran `python -m unittest tests.test_compose_thread_page tests.test_task_thread_pages`
  - Ran `python -m unittest tests.test_instance_info_page tests.test_board_index_page`
- Notes:
  - The board index and activity pages still use the separate front-page shell path at this stage; Stage 2 will migrate those outliers onto the canonical shell.

## Stage 2 - Migrate homepage and activity to the canonical shell
- Changes:
  - Moved the board index and activity pages off the separate front-page shell path so they now render through the shared header/footer flow.
  - Reworked `templates/board_index.html` and `templates/activity.html` into the same panel-based content framing used by interior pages while preserving their route-specific content.
  - Restored the moderation destination in the homepage action row and added the minimal board-index content styling needed after removing the old front-page wrapper.
  - Updated the board-index route test to assert the shared shell instead of the retired front-header path.
- Verification:
  - Ran `python -m unittest tests.test_board_index_page tests.test_site_activity_page`
  - Ran `python -m unittest tests.test_task_thread_pages tests.test_compose_thread_page tests.test_instance_info_page`
- Notes:
  - Front-page-specific CSS and helper branches still exist in the codebase as dead or transitional paths; Stage 3 will remove stale layout branches and add broader regression coverage.

## Stage 3 - Remove stale layout branches and lock coverage
- Changes:
  - Removed the dead `front-*` shell CSS and `page-shell-front` styling that no longer had active callers after the Stage 2 migration.
  - Kept only the board-index-specific content styling needed for the unified shell.
  - Added shared-shell assertions for the activity and task-priorities pages so representative routes now verify the canonical header/footer contract directly.
- Verification:
  - Ran `python -m unittest tests.test_board_index_page tests.test_site_activity_page tests.test_task_priorities_page`
  - Ran `python -m unittest tests.test_compose_thread_page tests.test_profile_update_page tests.test_task_thread_pages tests.test_instance_info_page`
- Notes:
  - The verification intentionally checks representative route families rather than every single page-specific copy string, so future shell refactors should keep these tests stable as long as the shared layout contract remains intact.
