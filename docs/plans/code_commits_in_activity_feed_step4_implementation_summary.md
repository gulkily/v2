## Stage 1 - Broaden repository commit classification
- Changes:
  - Extended `forum_web/web.py` so activity filtering recognizes `code` and the helper layer can load repository-wide commits instead of only `records/posts` changes.
  - Added deterministic commit classification rules for content, moderation, and code activity, with code taking precedence for mixed commits that touch both source and record files.
  - Expanded `tests/test_site_activity_git_log_helpers.py` to cover repository-wide commit loading, explicit classification, and the new `code` filter mode.
  - Synced the approved Step 3 plan wording in `docs/plans/code_commits_in_activity_feed_step3_development_plan.md` so the planning artifact matches the approved implementation boundary.
- Verification:
  - Ran `python -m unittest tests.test_site_activity_git_log_helpers`
  - Ran `python -m unittest tests.test_site_activity_page`
- Notes:
  - This stage changes only the helper/model layer. `/activity/` still renders the existing content-plus-moderation UI until Stage 2 adds code commits to the page itself.

## Stage 2 - Render code commits on `/activity/`
- Changes:
  - Extended `forum_web/web.py` so `/activity/` exposes a fixed `code` filter, passes commit activity type into the shared commit-card rendering, and uses code-specific fallback copy when a commit has no canonical post targets.
  - Updated `templates/activity.html` and the activity page framing so the page reads as a broader repository activity stream rather than only content-plus-moderation history.
  - Expanded `tests/test_site_activity_page.py` with a code-commit fixture and assertions covering default timeline ordering plus the new `code` filter behavior.
- Verification:
  - Ran `python -m unittest tests.test_site_activity_page`
  - Ran `python -m unittest tests.test_site_activity_git_log_helpers`
- Notes:
  - Code commits still render as concise commit cards rather than diff views; this stage keeps `/activity/` out of git-browser territory.

## Stage 3 - Align repository-history labels and coverage
- Changes:
  - Updated `forum_web/web.py` so the shared page shell and board index action copy present `/activity/` as repository history while preserving `/moderation/` as a compatibility redirect into the filtered activity view.
  - Expanded `tests/test_board_index_page.py` and `tests/test_site_activity_page.py` so the broader repository-history wording is covered alongside the existing filter and redirect behavior.
- Verification:
  - Ran `python -m unittest tests.test_board_index_page`
  - Ran `python -m unittest tests.test_site_activity_page`
- Notes:
  - The route structure did not change in this stage; only the user-facing framing and regression coverage were tightened around the broader repository-history role.
