## Stage 1
- Goal: define the merged activity-event model and fixed filter modes without changing routes yet.
- Dependencies: approved Step 2; existing git-driven activity helpers; existing moderation-record read model.
- Expected changes: add one shared merged-feed helper layer that can collect git activity items and moderation items into a single ordered event list, plus a small fixed filter parser for modes such as `all`, `content`, and `moderation`; planned contracts such as `activity_filter_mode_from_request(raw_mode) -> str`, `load_activity_events(repo_root, *, mode: str, limit: int) -> list[ActivityEvent]`, and `sort_activity_events(events) -> list[ActivityEvent]`; no database changes.
- Verification approach: exercise the new helper layer with a disposable repo containing both git-backed content activity and moderation records, then confirm the filter modes return the expected subsets in stable order.
- Risks or open questions:
  - choosing one clear ordering model for mixed git and moderation items
  - keeping the merged event shape small instead of drifting into a generalized event framework
- Canonical components/API contracts touched: `fetch_recent_commits(...)`; moderation-record loading/slicing; new merged activity helper layer.

## Stage 2
- Goal: render the merged filtered feed on `/activity/`.
- Dependencies: Stage 1; current `/activity/` route and template; existing moderation-card rendering.
- Expected changes: extend `render_site_activity_page()` and `templates/activity.html` so `/activity/` becomes the canonical merged page with fixed filter controls, mixed event cards, and the existing repository snapshot panel; adapt moderation entry rendering for the merged page rather than maintaining a separate moderation-only layout as the primary path; planned contracts such as `render_activity_filter_nav(current_mode) -> str` and `render_activity_event_card(event, identity_context) -> str`.
- Verification approach: manually load `/activity/` in each filter mode and confirm the page keeps the snapshot panel, shows mixed events in default mode, and shows only the selected event type in filtered modes.
- Risks or open questions:
  - keeping moderation items visually understandable inside the activity feed
  - avoiding template duplication between activity and moderation rendering
- Canonical components/API contracts touched: `/activity/`; `templates/activity.html`; moderation card rendering; shared page layout/components.

## Stage 3
- Goal: consolidate navigation and lock the merged behavior into focused regression coverage.
- Dependencies: Stages 1-2; current `/moderation/` route and board-index navigation.
- Expected changes: reduce `/moderation/` to a compatibility path into the merged filtered activity view or otherwise remove it as a primary destination, update navigation so users are steered to the canonical combined history page, and add focused tests for merged ordering, filter behavior, and compatibility-route handling; planned contracts such as `moderation_log_redirect_target() -> str` if a redirect/compatibility handoff is used.
- Verification approach: request `/activity/` in all filter modes, request `/moderation/`, and confirm users end up on the merged experience with predictable output; run targeted unittest coverage for merged feed ordering and filter behavior.
- Risks or open questions:
  - deciding whether `/moderation/` should redirect or render a compatibility wrapper in the first slice
  - keeping tests stable while the merged page contains two entry types with different metadata
- Canonical components/API contracts touched: `/moderation/`; board-index activity/moderation navigation; merged-feed tests and compatibility behavior.
