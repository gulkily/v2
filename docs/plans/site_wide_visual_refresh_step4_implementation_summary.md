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

## Stage 2 - Read-surface restyle
- Changes:
  - Restyled the thread, post, moderation, instance info, and profile templates around shared page-section, page-lede, link-cluster, and detail-grid structures.
  - Extended the shared stylesheet so read surfaces use the calmer layout language for breadcrumbs, post cards, identity details, and metadata groups.
- Verification:
  - Ran `python -m unittest tests.test_instance_info_page tests.test_task_thread_pages tests.test_profile_update_page` and confirmed all 11 tests passed.
  - Ran a direct shell smoke check with `python - <<'PY' ... render_not_found() ... PY` and confirmed standard pages now render through the new `site-header--page` shell.
- Notes:
  - This stage keeps existing routes and content hierarchy intact while shifting the read surfaces onto the refreshed visual system.
