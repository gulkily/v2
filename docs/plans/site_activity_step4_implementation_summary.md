## Stage 1 - Surface git metadata to the UI frame
- Changes: Added helpers in `forum_web/web.py` to load the latest canonical records, gather identity context, and summarize the repository git metadata for downstream rendering.
- Verification: `python - <<'PY'
from forum_web.web import build_site_activity_context
context = build_site_activity_context(limit=1)
print(context['git_commit_id'])
print(len(context['recent_records']))
PY`
- Notes: git metadata reuses `load_instance_info`; caching can be introduced later if command latency becomes noticeable.

## Stage 2 - Wire the activity template
- Changes: Added `templates/activity.html`, `render_site_activity_page()`, and the new `/activity/` route, plus `tests/test_site_activity_page.py` to cover the feed and git metadata panel; each post card now surfaces a formatted timestamp and the git metadata panel shows the worktree status.
- Verification: `python -m pytest tests/test_site_activity_page.py`
- Notes: The template reuses the front layout and `post-card` markup so the activity feed stays aligned with the board index styling.

## Stage 3 - Point the board action at activity
- Changes: Rewired `render_board_index_action_links()` to surface `/activity/`, added a footer “moderation log” link so `/moderation/` remains reachable, and adjusted `tests/test_board_index_page.py` to assert the new action text while keeping a footer link to `/moderation/`.
- Verification: `python -m pytest tests/test_board_index_page.py`
- Notes: The board index action chips now steer readers toward the new activity view, and the footer now houses the moderation log link for moderators.
