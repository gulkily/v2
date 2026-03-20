## Stage 1
- Goal: add a paged activity retrieval layer that can return one page of matching events for each `view` mode without relying on the current “fetch 12 global commits then filter” behavior.
- Dependencies: approved Step 2; existing activity filter parsing; existing git commit and moderation record loaders.
- Expected changes: extend the activity helper layer in `forum_web/web.py` to parse pagination parameters, define a stable page size, and fetch enough matching items for `content`, `code`, `moderation`, and `all`; planned contracts such as `activity_page_from_request(raw_page) -> int`, `load_activity_events(repo_root, *, mode: str, page: int, page_size: int) -> PagedActivityResult`, and helper logic for paged filtered commit retrieval.
- Verification approach: add helper-level tests that exercise each mode across more than one page of mixed history and confirm page 1/page 2 return the expected matching subsets in stable order.
- Risks or open questions:
  - choosing a simple, stable paging contract for the merged `all` view
  - avoiding expensive repeated git scans while still filling per-view pages accurately
- Canonical components/API contracts touched: `activity_filter_mode_from_request(...)`; `load_activity_events(...)`; git commit classification/retrieval helpers; moderation record slicing.

## Stage 2
- Goal: render pagination controls on `/activity/` and preserve filter state while moving between older and newer result pages.
- Dependencies: Stage 1; existing `/activity/` route and template; current filter-nav rendering.
- Expected changes: extend `render_site_activity_page()` and `templates/activity.html` to pass page-state context, render older/newer navigation, and preserve `view` plus `page` in generated links; planned contracts such as `render_activity_pagination_nav(*, current_mode: str, page: int, has_next_page: bool) -> str`.
- Verification approach: manually request `/activity/` with `view` and `page` combinations, confirm pagination links appear only when needed, and confirm switching filters keeps users on page 1 of the selected view unless explicitly paged.
- Risks or open questions:
  - making the pagination controls clear without adding visual clutter to the activity page
  - ensuring empty or out-of-range pages degrade predictably
- Canonical components/API contracts touched: `/activity/`; `templates/activity.html`; activity filter nav and page rendering helpers.

## Stage 3
- Goal: lock the paginated behavior into focused regression coverage and verify the corrected per-view counts against realistic mixed activity histories.
- Dependencies: Stages 1-2; current activity page and helper tests.
- Expected changes: expand activity helper/page tests to cover page boundaries, per-view counts, `all` merged ordering across multiple pages, and request-operation metadata for paginated activity requests; adjust existing expectations that assumed one fixed 12-item recent window per filter.
- Verification approach: run targeted tests such as `python -m pytest tests/test_site_activity_page.py tests/test_site_activity_git_log_helpers.py tests/test_request_operation_events.py` and manually spot-check `/activity/?view=content&page=2`, `/activity/?view=code&page=2`, and `/activity/?view=all&page=2`.
- Risks or open questions:
  - keeping tests deterministic when git commit dates are close together
  - avoiding brittle HTML assertions for pagination controls
- Canonical components/API contracts touched: activity page tests; activity helper tests; request-operation timing/metadata coverage.
