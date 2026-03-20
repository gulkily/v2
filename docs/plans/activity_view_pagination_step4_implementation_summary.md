## Stage 1 - Add paged activity retrieval helpers per filter
- Changes:
  - added shared activity paging contracts in `forum_web/web.py`, including `activity_page_from_request(...)`, `PagedActivityResult`, and paged retrieval for `content`, `code`, `moderation`, and merged `all`
  - changed activity loading so filtered views page through their own matching history instead of filtering only the latest global commit slice
  - updated helper tests to cover page parsing, content pagination, and merged `all` pagination behavior
- Verification:
  - `python -m pytest tests/test_site_activity_git_log_helpers.py`
- Notes:
  - the page renderer still does not expose pagination controls yet; this stage establishes the backend paging contract that later stages will surface in `/activity/`

## Stage 2 - Render paginated activity navigation on `/activity/`
- Changes:
  - wired the `/activity/` route to accept a `page` query parameter and pass it through the shared paged activity helper
  - added older/newer pagination controls to `templates/activity.html` while preserving the existing filter-chip navigation
  - removed the older repository snapshot module so the page focuses on the paginated activity stream itself
  - added page-level regression coverage for content-view pagination links and page-to-page result changes
- Verification:
  - `python -m pytest tests/test_site_activity_page.py`
- Notes:
  - request-operation metadata and broader regression coverage for paginated activity requests are deferred to Stage 3

## Stage 3 - Lock paginated activity behavior into focused regression coverage
- Changes:
  - extended request-operation tests so `/activity/` records both `view` and `page` metadata for paginated requests
  - ran the combined helper, page, and request-level activity regression set against the new pagination behavior
  - kept the implementation scoped to the current read model and route contract; no new event store or route family was introduced
- Verification:
  - `python -m pytest tests/test_site_activity_git_log_helpers.py tests/test_site_activity_page.py tests/test_request_operation_events.py`
- Notes:
  - the current implementation uses numbered GET pagination and preserves the existing `view` filter model across all activity sections
