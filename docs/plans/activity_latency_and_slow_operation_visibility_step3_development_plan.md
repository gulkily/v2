1. Goal: make slow `/activity/` requests visible and diagnosable through the existing operation-events surface.
Dependencies: approved Step 2; current request-operation wrapper in `forum_web/web.py`; current recent-operations query in `forum_core/operation_events.py`.
Expected changes: add route-specific timing steps and `view` metadata for `/activity/` requests through the existing request-operation model; refine the recent-operations read path so the panel stays recency-first and only surfaces operations slower than the agreed threshold rather than being dominated by older longest-duration entries. Planned contracts may include an expanded `load_recent_operations(...)` read shape or a separate helper such as `load_recent_slow_operations(...)`; no database schema change expected.
Verification approach: manually request `/activity/` and `/activity/?view=code`, then open the project info page and confirm the recent-operations panel surfaces those request entries with route-specific timing detail.
Risks or open questions:
- keeping the operator panel simple while still making `/activity/` requests easy to spot
Canonical components/API contracts touched: request-operation wrapper; `forum_core.operation_events`; existing recent-operations panel in `forum_web.web`.

2. Goal: reduce avoidable work in the `/activity/` route without changing the route or filter contract.
Dependencies: Stage 1; current activity helper path in `forum_web/web.py`.
Expected changes: trim expensive activity-page work using the new timing visibility, likely by narrowing view-specific loading and avoiding unnecessary repository, git, or post-resolution work on filtered activity requests while preserving the current visible output for `/activity/?view=all|content|moderation|code`; optimize `git_status_summary()` freely so long as the page still shows equivalent operator-facing information. Planned contracts may include smaller helper boundaries around activity-event loading, commit/post resolution, or git summary loading; no new route and no database change expected.
Verification approach: manually compare `/activity/` load behavior before and after for `all`, `moderation`, and `code` views and confirm the expected timing steps shrink while page content and filters remain intact.
Risks or open questions:
- which current helper is the dominant cost once route-specific timings are visible
- avoiding regressions in commit-card content while reducing route work
Canonical components/API contracts touched: `/activity/`; existing activity filter parsing; activity-event/card helpers; git-summary read path only as reused by the page.

3. Goal: lock the visibility fix and activity-route improvement into focused regression coverage.
Dependencies: Stages 1-2; current request-operation, activity-page, and operation-event tests.
Expected changes: extend `tests/test_request_operation_events.py`, `tests/test_site_activity_page.py`, and operation-event or project-info coverage so slow activity requests, recent-panel ordering/selection behavior, and preserved activity filters are all exercised through the existing request path; keep coverage minimal and focused on the route/request path rather than adding a heavy performance harness; update the Step 4 summary during implementation, but no new user docs are expected unless the panel wording materially changes.
Verification approach: run the targeted unittest files, then manually request `/activity/` plus the project info page to confirm the operations panel and route content agree with the tests.
Risks or open questions:
- building fixtures heavy enough to catch the visibility bug without making tests fragile
- avoiding overlap between generic operation-event tests and route-specific activity tests
Canonical components/API contracts touched: `tests/test_request_operation_events.py`; `tests/test_site_activity_page.py`; operation-event read behavior as rendered on the existing project info page.
