## Stage 1 - Canonical rebuild status contract
- Changes:
  - Added a non-streaming post-index rebuild status contract in `forum_web/web.py` for CGI/PHP-style requests.
  - Covered indexed-read requests on buffered hosts now return an immediate `503 Service Unavailable` response with explicit rebuild-status headers instead of falling straight into the blocking rebuild.
  - Preserved the existing streamed same-request behavior on long-lived Python hosts.
- Verification:
  - `python -m unittest tests.test_post_index_startup tests.test_request_operation_events`
- Notes:
  - The buffered-host contract includes the original target path and a dedicated rebuild request path so the PHP adapter can render an immediate status page without duplicating rebuild detection logic.
