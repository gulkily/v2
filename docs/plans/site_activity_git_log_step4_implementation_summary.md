## Stage 1 - Fetch git commits and resolve records
- Changes: Added `GitCommitEntry`, `fetch_recent_commits`, `build_posts_index`, and `resolve_commit_posts` helpers in `forum_web/web.py` to shell out to `git log`, parse commit metadata, and map touched files back to canonical posts.
- Verification: `python -m pytest tests/test_site_activity_git_log_helpers.py`
- Notes: Helpers limit the log to commits touching `records/posts`; follow-up stages will reuse this context when rendering the activity feed.

## Stage 2 - Render git commits as activity items
- Changes: Replaced the `/activity/` rendering with commit-driven cards, added `render_commit_card` plus commit-date formatting helpers, refreshed `templates/activity.html`/`site.css`, and updated `tests/test_site_activity_page.py` to expect the git-driven layout.
- Verification: `python -m pytest tests/test_site_activity_page.py`
- Notes: Each commit card reuses `post-card` markup for the touched records and keeps the list newest-first while keeping the repository snapshot panel intact.

## Stage 3 - Verify navigation remains aligned
- Changes: Confirmed the board index action still points at `/activity/` and the moderation log stays accessible through the footer after this rewrite.
- Verification: `python -m pytest tests/test_board_index_page.py`
- Notes: This stage simply validates that the fallback navigation tests still pass now that the activity feed is git-driven.
