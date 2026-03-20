## Stage 1 - Add paged activity retrieval helpers per filter
- Changes:
  - added shared activity paging contracts in `forum_web/web.py`, including `activity_page_from_request(...)`, `PagedActivityResult`, and paged retrieval for `content`, `code`, `moderation`, and merged `all`
  - changed activity loading so filtered views page through their own matching history instead of filtering only the latest global commit slice
  - updated helper tests to cover page parsing, content pagination, and merged `all` pagination behavior
- Verification:
  - `python -m pytest tests/test_site_activity_git_log_helpers.py`
- Notes:
  - the page renderer still does not expose pagination controls yet; this stage establishes the backend paging contract that later stages will surface in `/activity/`
