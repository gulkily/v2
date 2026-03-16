# Site Activity Step 3: Development Plan

## Stage 1 – Surface git metadata to the UI frame
- Goal: Provide the “git commit fingerprint/date + optional status” data we plan to show on `/activity/` without touching templates yet.
- Dependencies: Existing helpers under `forum_web/repository.py` (git helpers used by `/instance/`) and the record-loading functions that power the board index/thread views.
- Expected changes: Add a `render_site_activity_page(context)` helper in `forum_web/web.py` that calls a new `load_recent_records(limit)` helper (reusing whatever the board index already uses) and a `git_status_summary()` helper that calls `git rev-parse HEAD` plus `git show --no-patch --format=%cd` (or reuse `render_instance_info_page` helpers). Return the combined data in a context dict for the template.
- Verification: Load `/activity/` manually (or via tests once Stage 2 lands) and confirm git metadata is available in the response payload before templating is applied.
- Risks/Open questions: Ensure we don’t shell out excessively every request; we can cache the git metadata briefly if needed based on how `/instance/` already works.
- Canonical components touched: `render_instance_info_page()` helpers (`forum_web/web.py`) for git data, record-loading logic shared with board index/thread templates.

## Stage 2 – Create the `/activity/` template using existing post card markup
- Goal: Build a layout that renders the recent canonical records (threads/replies) and the git metadata panel described in the requirements.
- Dependencies: `render_post_card()` (or similar) for per-record markup, `templates/base.html` for hero layout, and the context produced in Stage 1.
- Expected changes: Introduce `templates/activity.html` that iterates over `record_cards_html` (rendered via `render_post_card`) and displays git metadata in a sidebar/panel. Hook the new template to the helper from Stage 1 so `/activity/` renders a calm layout while reusing existing CSS classes.
- Verification: Render `/activity/` (maybe via `tests/test_board_index_page.py` extended or new test) and ensure the template includes at least one post card and the git metadata strings (commit ID/date).
- Risks/Open questions: Determine whether we limit to the latest N canonical records or include replies/threads; reuse board index record-fetching logic for consistency.
- Canonical components touched: `render_post_card()` for the feed, `templates/base.html` hero/section frame.

## Stage 3 – Update board index navigation + tests to point at `/activity/`
- Goal: Swap the existing “view moderation log” chip for a “view site activity” action linking to the new page while keeping `/moderation/` discoverable elsewhere.
- Dependencies: `render_board_index_action_links()` and the board header markup (no new templates).
- Expected changes: Update `render_board_index_action_links()` in `forum_web/web.py` so the moderation link is replaced with `/activity/` + new label, add a footer/nav link to `/moderation/` (if helpful), and add/adjust tests to assert the new label/URL is present and the old one is gone.
- Verification: Run unit tests (or add new ones) to verify the board index action includes the new activity link and the moderation link is still reachable through another UI element (footer / side panel); load `/` to confirm the new chip appears.
- Risks/Open questions: Make sure accessibility semantics/patterns remain consistent when we swap the chip; confirm there is still a path to `/moderation/`.
