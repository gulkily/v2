## Stage 1 - Shared shell and homepage cleanup
- Changes:
  - Replaced the default hero-based shared page header with a calmer site-wide header/footer shell used by non-homepage pages.
  - Updated the shared CSS variables and default panel/chip styling toward the new visual language.
  - Removed the homepage's "Browse by board tag" section from `templates/board_index.html`.
- Verification:
  - Ran `python -m unittest tests.test_compose_thread_page tests.test_instance_info_page tests.test_task_priorities_page` and confirmed all 12 tests passed.
  - Ran a direct homepage render smoke check with `python - <<'PY' ... render_board_index() ... PY` and confirmed `Browse by board tag` is absent while the existing front-page header remains.
- Notes:
  - This stage changes the shared frame and homepage cleanup only; page-specific template restyling follows in later stages.
