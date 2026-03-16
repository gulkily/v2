## Stage 1 - Homepage render context
- Changes:
  - Added homepage-specific board-index context helpers for stats, action links, compact thread rows, and sidebar modules.
  - Updated `render_board_index()` to build its template context through the new helper layer instead of assembling everything inline.
- Verification:
  - Ran `python -m unittest tests.test_instance_info_page tests.test_task_priorities_page` and confirmed all 10 tests passed.
- Notes:
  - This stage only reshapes render data and keeps the visible homepage structure largely unchanged; Stage 2 will replace the layout.
