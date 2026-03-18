## Stage 1 - Homepage render context
- Changes:
  - Added homepage-specific board-index context helpers for stats, action links, compact thread rows, and sidebar modules.
  - Updated `render_board_index()` to build its template context through the new helper layer instead of assembling everything inline.
- Verification:
  - Ran `python -m unittest tests.test_instance_info_page tests.test_task_priorities_page` and confirmed all 10 tests passed.
- Notes:
  - This stage only reshapes render data and keeps the visible homepage structure largely unchanged; Stage 2 will replace the layout.

## Stage 2 - Homepage layout and shell
- Changes:
  - Extended the shared page renderer so `/` can supply a custom header and footer without forcing that structure onto the rest of the site.
  - Replaced the homepage template with a ZenMemes-inspired text-first layout and added homepage-specific styles for the new header, thread stream, sidebar, and footer.
- Verification:
  - Ran `python -m unittest tests.test_instance_info_page tests.test_task_priorities_page` and confirmed all 10 tests passed.
  - Ran a direct render smoke check with `python - <<'PY' ... render_board_index() ... PY` and confirmed the output contains `front-header`, `front-layout`, `Threads worth opening`, `compose a signed thread`, `instance info`, and `task priorities`.
- Notes:
  - The homepage now uses a dedicated front-page shell while thread, detail, and planning pages still use the existing hero-based layout.

## Stage 3 - Homepage regression coverage
- Changes:
  - Added a dedicated homepage test module that asserts the new front-page structure, repository-backed thread rendering, board-tag anchors, and preserved destination links.
- Verification:
  - Ran `python -m unittest tests.test_board_index_page tests.test_instance_info_page tests.test_task_priorities_page` and confirmed all 12 tests passed.
- Notes:
  - The new assertions target stable structural markers and key links rather than every line of display copy, which keeps the tests useful without making future copy edits expensive.
