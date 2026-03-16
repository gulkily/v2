## Stage 1 - Surface git metadata to the UI frame
- Changes: Added helpers in `forum_web/web.py` to load the latest canonical records, gather identity context, and summarize the repository git metadata for downstream rendering.
- Verification: `python - <<'PY'\nfrom forum_web.web import build_site_activity_context\ncontext = build_site_activity_context(limit=1)\nprint(context['git_commit_id'])\nprint(len(context['recent_records']))\nPY`
- Notes: git metadata reuses `load_instance_info`; caching can be introduced later if command latency becomes noticeable.

-## Stage 2 - Wire the activity template
- Changes: Added `templates/activity.html`, `render_site_activity_page()`, and the new `/activity/` route, plus `tests/test_site_activity_page.py` to cover the feed and git metadata panel; each post card now surfaces a formatted timestamp and the git metadata panel shows the worktree status.
- Verification: `python -m pytest tests/test_site_activity_page.py`
- Notes: The template reuses the front layout and `post-card` markup so the activity feed stays aligned with the board index styling.
