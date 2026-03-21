## Stage 1 - Canonical rebuild status contract
- Changes:
  - Added a non-streaming post-index rebuild status contract in `forum_web/web.py` for CGI/PHP-style requests.
  - Covered indexed-read requests on buffered hosts now return an immediate `503 Service Unavailable` response with explicit rebuild-status headers instead of falling straight into the blocking rebuild.
  - Preserved the existing streamed same-request behavior on long-lived Python hosts.
- Verification:
  - `python -m unittest tests.test_post_index_startup tests.test_request_operation_events`
- Notes:
  - The buffered-host contract includes the original target path and a dedicated rebuild request path so the PHP adapter can render an immediate status page without duplicating rebuild detection logic.

## Stage 2 - PHP-host rebuild status page
- Changes:
  - Extended `php_host/public/index.php` to detect the canonical rebuild-status contract and render an immediate self-contained waiting page on the Apache/PHP path.
  - The PHP status page now launches the blocking rebuild in a hidden same-origin iframe request against the dedicated rebuild path, then redirects back to the original URL when that request finishes.
  - Updated `php_host/public/cache.php` so rebuild-control requests bypass the PHP microcache, and added a PHP-host integration test for the status-page flow.
- Verification:
  - `python -m unittest tests.test_post_index_startup tests.test_php_host_cache`
- Notes:
  - The initial public request returns immediately on the buffered host, but the actual rebuild still runs synchronously in the hidden follow-up request because the PHP/CGI path has no durable background worker.

## Stage 3 - Regression coverage for the buffered handshake
- Changes:
  - Added coverage in `tests/test_post_index_startup.py` that the dedicated CGI/PHP rebuild request bypasses the temporary status contract and enters the canonical blocking path.
  - Re-ran the broader covered suite across startup behavior, PHP host behavior, route rendering, request operations, and the CGI gateway boundary.
- Verification:
  - `python -m unittest tests.test_post_index_startup tests.test_request_operation_events tests.test_php_host_cache tests.test_board_index_page tests.test_username_profile_route tests.test_wsgi_gateway`
- Notes:
  - The buffered host path is now locked into an explicit two-request handshake: one immediate status response, then one blocking rebuild request that hands the user back to the original page when it completes.
