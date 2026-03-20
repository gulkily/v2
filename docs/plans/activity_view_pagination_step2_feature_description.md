## Problem
`/activity/` currently shows only a small recent slice of each activity filter, and each filtered view is derived from a limited recent commit window rather than from the full matching history of that view. Users need to be able to browse all activity for `all`, `content`, `moderation`, and `code` with pagination, so each section can be explored beyond the first page without introducing a new event store or a separate activity route structure.

## User Stories
- As a site user, I want to browse older items in each activity section so I can review more than the newest handful of events.
- As a reader, I want pagination to stay within the current filter view so I can continue paging through content, moderation, or code without losing context.
- As an operator, I want the activity page to expose a complete navigable history per view so I can audit older repository and moderation activity without switching to ad hoc git commands.
- As a maintainer, I want pagination to reuse the current git-commit and moderation-record read models so this remains a read-side extension rather than a broader backend rewrite.

## Core Requirements
- The slice must keep `/activity/` as the canonical route and preserve the current `view=all|content|moderation|code` filter model.
- The slice must add pagination to each view so users can move beyond the first page of results using stable GET parameters.
- Each filtered view must page through its own matching dataset rather than filtering only the latest global commit slice.
- `view=content` must include content-classified repository commits across the relevant `records/` areas, `view=code` must include code-classified commits, and `view=moderation` must page through moderation records directly.
- `view=all` must continue to present one ordered merged timeline and support pagination over that merged ordering.
- The page must expose clear navigation for moving to older and newer pages while preserving the selected filter.
- The feature must stay read-only and must not introduce a database migration, a new durable event table, or a separate client-side infinite-scroll requirement.

## Shared Component Inventory
- Existing canonical activity route in `forum_web/web.py`: extend this route because the feature is pagination on the current activity surface, not a new page family.
- Existing activity filter controls and page template in `templates/activity.html`: extend this shared template to render pagination controls while keeping the current filter navigation.
- Existing git-based activity read helpers such as `fetch_recent_repository_commits(...)`, `classify_commit_activity(...)`, and commit-card rendering: extend these helpers to support paged filtered retrieval rather than replacing the read model.
- Existing moderation read helpers such as `load_moderation_records(...)` and `moderation_log_slice(...)`: reuse these for moderation pagination rather than inventing a second moderation data path.
- Existing merged event model in `load_activity_events(...)`: extend this as the canonical place where `all`, `content`, `moderation`, and `code` paging rules are coordinated.

## Simple User Flow
1. User opens `/activity/` and lands on the default filtered activity view.
2. The page shows one page of events plus navigation to older results when more matching items exist.
3. The user switches to `content`, `moderation`, `code`, or `all`; the page keeps the selected filter and shows page-appropriate results for that activity type.
4. The user clicks `Older` or `Newer` and continues browsing within the same filter view.
5. The user opens an event card to inspect the underlying post, moderation record, or commit context as before.

## Success Criteria
- Each activity filter view can be paged beyond the initial results set.
- Filtered views are populated from their own matching activity history rather than from a truncated global commit window.
- The current `/activity/` route and filter model remain intact and linkable through GET parameters.
- Users can move forward and backward through paginated activity results without losing their selected filter.
- The implementation remains read-only and reuses the current git and moderation read models rather than introducing a new storage layer.
