# Site Activity Git Log Step 3: Development Plan

## Stage 1 – Stream git log entries and resolve touched records
- Goal: Pull the latest N commits from `git log` and resolve which record files (posts/replies) were touched per commit so we can render commit metadata plus canonical post links.
- Dependencies: `git log` command, existing post-loading helpers from `forum_web/repository.py`, and the records directory layout to map file paths to post IDs via `load_posts()`/`index_posts()`.
- Expected changes: Add helper(s) such as `fetch_recent_commits(limit)` and `resolve_commit_records(commit)` that shell out to git, parse commit metadata (hash, date, summary, changed files), and look up the related `Post` objects by path. No UI changes yet.
- Verification: Run the helper(s) manually (e.g., via a temporary script or REPL) to confirm they return commits with attached `Post` metadata sorted by commit date, and add unit tests for the new helpers.
- Risks/Open questions: Shelling out to git may be slower; we should consider caching/limit, and ensure we only include commits that actually touch canonical records.
- Canonical components touched: `load_posts()`/`index_posts()` (for lookup) and `forum_web/web.py` (where the helpers live).

## Stage 2 – Render git commits as activity items
- Goal: Replace the current record-driven loop on `/activity/` with a git-commit-driven list that includes the commit fingerprint/date and links to the canonical posts it touched.
- Dependencies: The context produced by Stage 1, `templates/activity.html`, and `render_post_card()` for linking back into records.
- Expected changes: Update `render_site_activity_page()` to iterate through the commit list, create per-commit HTML (maybe using a new helper like `render_commit_card(commit, posts)` that reuses `post-card` markup), ensure the list remains newest-first, and update the template to reflect commit-focused content (fingerprint, date, message, linked posts).
- Verification: Load `/activity/` and verify the page shows git commits in descending order with fingerprints/dates and links to posts; add tests covering the new rendering logic.
- Risks/Open questions: A single commit may touch multiple posts—decide how to display them without repeating the commit row or cluttering the UI.
- Canonical components touched: `templates/activity.html`, `render_post_card`.

## Stage 3 – Refresh tests and navigation
- Goal: Update navigation/tests to confirm `/activity/` is the board index action and the git-driven list behaves as expected.
- Dependencies: `tests/test_board_index_page.py` (new expectations for the action chip) and a new test module covering `/activity/` content order.
- Expected changes: Adjust board index tests to assert “view site activity,” add/extend `/activity/` tests to verify chronological order and commit metadata, and ensure the moderation log link remains accessible elsewhere.
- Verification: `python -m pytest tests/test_board_index_page.py tests/test_site_activity_page.py` (updated) plus any new commit-order tests.
- Risks/Open questions: If git log parsing changes output (e.g., timezone), ensure tests are robust.
