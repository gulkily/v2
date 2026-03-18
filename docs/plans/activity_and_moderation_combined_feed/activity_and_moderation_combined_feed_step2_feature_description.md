## Problem
The app currently splits instance history across two nearby read surfaces: `/activity/` shows git-driven site activity, while `/moderation/` shows signed moderation records on a separate page. The next slice should combine those into one canonical activity page with explicit filters so operators and readers can inspect all recent instance events from one place without introducing a broader event-system rewrite.

## User Stories
- As a developer, I want one canonical activity page that includes both site activity and moderation events so that the instance history is no longer split across two similar pages.
- As an operator, I want fixed filters on that page so that I can quickly switch between all activity, content activity, and moderation activity.
- As a reader, I want the merged page to preserve the current activity context and moderation auditability so that I can still understand what happened and why.
- As a maintainer, I want the merged page to reuse the existing activity and moderation read models so that this stays a focused page consolidation rather than a new generalized event system.

## Core Requirements
- The slice must provide one canonical web page for combined instance activity, using explicit fixed filters for at least all activity, content activity, and moderation activity.
- The slice must preserve the existing git-driven activity entries and the existing signed moderation record visibility rather than dropping one side of the current history.
- The slice must keep a clear ordering model for mixed entries so the merged page remains predictable and auditable.
- The slice must keep the work scoped to read-side consolidation and filtering, not a broader rewrite of moderation actions, git history semantics, or a new event-storage model.
- The slice must keep existing navigation coherent so users can reach the combined page through the normal activity entry point.

## Shared Component Inventory
- Existing canonical activity route: extend `/activity/` in `forum_web/web.py` as the one merged page because it already serves as the broader site-history surface.
- Existing git activity read model: reuse the current `fetch_recent_commits(...)`, `resolve_commit_posts(...)`, and commit-card rendering path that already powers `/activity/`.
- Existing moderation read model: reuse `load_moderation_records(...)`, `moderation_log_slice(...)`, and moderation-card rendering rather than inventing a new moderation event source.
- Existing activity template surface: extend `templates/activity.html` as the merged page shell because it already contains the canonical activity page framing and repository snapshot panel.
- Existing moderation entry rendering: reuse or adapt the current moderation card rendering from the moderation log route so moderation events stay recognizable inside the merged page.
- Existing dedicated moderation route: either retire `/moderation/` as a primary destination or reduce it to a compatibility path into the merged filtered activity view; no separate long-term duplicate log should remain.

## Simple User Flow
1. A reader opens `/activity/` and lands on the merged instance-history page.
2. The page shows a default combined activity stream that includes both git-driven content activity and moderation events in one ordered list.
3. The reader uses fixed filter controls to switch between all activity, content activity, and moderation activity.
4. The page updates to show only the selected event class while preserving the same overall page structure and ordering model.
5. The reader follows a content or moderation item to the existing underlying thread, post, or moderation context as needed.

## Success Criteria
- `/activity/` becomes the canonical page for both site activity and moderation history.
- Users can filter the merged page by at least all activity, content activity, and moderation activity without navigating to a separate moderation log page.
- Existing git-driven activity entries and moderation records both remain visible and understandable on the merged page.
- The merged page uses one stable ordering model across filter modes.
- Navigation now points users to one canonical combined history page instead of splitting them between separate activity and moderation destinations.
