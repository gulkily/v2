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
