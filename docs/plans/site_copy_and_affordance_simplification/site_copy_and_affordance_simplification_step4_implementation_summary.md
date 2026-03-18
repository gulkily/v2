## Stage 1 - Homepage affordance cleanup
- Changes:
  - Removed the non-functional homepage tag-link strip from the header and dropped the extra homepage sidebar explainer panels.
  - Simplified the homepage intro copy so the front page keeps only the core thread stream and working action links.
- Verification:
  - Ran `python -m unittest tests.test_board_index_page` and confirmed both homepage tests passed.
  - Ran a direct render smoke check with `python - <<'PY' ... render_board_index() ... PY` and confirmed `front-topic-strip`, `What this view is`, and `House style` are absent while the core action links remain present.
- Notes:
  - This stage removes unfinished or low-value homepage affordances only; broader read/write/planning copy cleanup follows in later stages.

## Stage 2 - Read and planning copy cleanup
- Changes:
  - Removed repeated explanatory paragraphs from thread, moderation, instance, profile, task priorities, and task detail templates.
  - Simplified section headings where the old labels repeated information the page layout already communicated, such as shortening profile and posts sections.
- Verification:
  - Ran `python -m unittest tests.test_instance_info_page tests.test_task_priorities_page tests.test_task_thread_pages tests.test_profile_update_page` and confirmed all 20 tests passed.
- Notes:
  - This stage is strictly subtractive: routes, actions, structured data, and planning controls remain intact while the pages carry less framing copy.

## Stage 3 - Write-surface copy cleanup
- Changes:
  - Removed repeated contextual and explanatory text from compose and profile-update pages while keeping the primary forms unchanged.
  - Renamed the optional disclosure from `Technical details` to `Advanced` and trimmed the repeated explanatory paragraphs inside that secondary section.
- Verification:
  - Ran `python -m unittest tests.test_compose_thread_page tests.test_compose_reply_page tests.test_profile_update_page` and confirmed all 7 tests passed.
- Notes:
  - The compose/profile-update DOM hooks, ids, data attributes, and primary actions remain unchanged; only the surrounding scaffolding text was reduced.

## Stage 4 - Regression coverage
- Changes:
  - Added representative absence checks for removed homepage affordances and trimmed copy on compose, profile-update, and task-priorities pages.
  - Kept the coverage focused on structural simplification markers so the tests confirm what was removed without becoming copy-fragile.
- Verification:
  - Ran `python -m unittest tests.test_board_index_page tests.test_compose_thread_page tests.test_profile_update_page tests.test_task_priorities_page tests.test_task_thread_pages tests.test_instance_info_page` and confirmed all 24 tests passed.
- Notes:
  - The assertions focus on removed affordances and renamed secondary disclosures, while the existing tests continue to cover key actions and hooks.
