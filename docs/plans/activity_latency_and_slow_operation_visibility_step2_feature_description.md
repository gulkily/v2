## Problem
`/activity/?view=...` feels slow for readers, and the current “Recent slow operations” panel does not reliably help an operator notice or diagnose those slow activity requests. The next slice should improve `/activity/` responsiveness while making slow activity loads visible through the existing in-app operation-events surface.

## User Stories
- As a reader, I want `/activity/` and its filtered `view` modes to load faster so that repository history feels usable instead of sluggish.
- As an operator, I want slow `/activity/` requests to show up in the existing recent slow operations surface so that I can tell when the route is regressing.
- As a maintainer, I want the activity route to expose enough route-specific timing detail through the current operation-event model so that I can reduce the slow work without guessing.

## Core Requirements
- The slice must improve perceived and actual load time for `/activity/` and its existing `view` filters without introducing a second activity route.
- Slow `/activity/` requests must become visible and identifiable in the existing recent slow operations surface.
- The feature must reuse the current request-operation event model and recent-operations panel rather than introducing a separate monitoring dashboard.
- The feature must preserve the current `/activity/` filter contract (`all`, `content`, `moderation`, `code`) and the current route shape `/activity/?view=...`.
- The slice must keep scope focused on `/activity/` performance and the visibility gap around recent slow operations, not broader whole-app observability work.

## Shared Component Inventory
- `/activity/` route and activity helpers in `forum_web/web.py`: extend the canonical route and helper path rather than creating a parallel activity endpoint.
- “Recent slow operations” panel in `forum_web/web.py`: extend this existing operator-facing read surface rather than adding a new report page.
- Operation-event store and loader in `forum_core/operation_events.py`: reuse and refine the current operation-event model/query path rather than inventing a second storage mechanism.
- Existing request and activity tests in `tests/test_request_operation_events.py`, `tests/test_site_activity_page.py`, and related operation-event tests: extend the current regression coverage rather than adding a separate test harness outside the existing request path.

## Simple User Flow
1. A reader opens `/activity/` or `/activity/?view=<mode>`.
2. The page loads faster than before while preserving the same filter choices and overall route behavior.
3. If an activity request is slow, the operator later opens the project info page and can see that recent slow activity request in the existing operations panel with enough context to recognize it.
4. A maintainer uses that route-specific timing visibility to confirm where activity-page work is spending time and to validate the improvement.

## Success Criteria
- `/activity/` remains on the same route and filter contract, but loads noticeably faster in normal use.
- A slow `/activity/` request is visible in the current recent slow operations surface with enough identifying context to distinguish its `view` mode.
- The recent-operations surface reflects recent slow activity requests instead of leaving them effectively hidden behind unrelated older operations.
- Existing activity-page and request-operation behavior remains intact aside from the targeted performance and visibility improvements.
