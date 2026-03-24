## Stage 1 - Define the static-public-read contract
- Changes:
  - Added a distinct static-HTML route eligibility contract in [`cache.php`](/home/wsl/v2/php_host/public/cache.php) with `forum_static_html_request_path(...)`, `forum_static_html_request()`, `forum_static_html_dir()`, and `forum_static_html_public_path(...)`.
  - Kept the contract narrower than the PHP microcache allowlist by excluding APIs, query-string variants, and profile subroutes such as `/update` and `/merge`.
  - Extended [`forum_host_config.example.php`](/home/wsl/v2/php_host/public/forum_host_config.example.php) with a `static_html_dir` setting for a public artifact root.
  - Added focused PHP helper tests in [`test_php_host_cache.py`](/home/wsl/v2/tests/test_php_host_cache.py) for static-route eligibility and path mapping.
- Verification:
  - Ran `python -m unittest tests.test_php_host_cache.PhpHostCacheTests.test_static_html_request_only_allows_safe_anonymous_html_routes tests.test_php_host_cache.PhpHostCacheTests.test_static_html_public_path_maps_allowlisted_routes_to_index_files tests.test_php_host_cache.PhpHostCacheTests.test_php_host_caches_allowlisted_reads_and_marks_hit_headers`
  - Result: 3 tests passed.
- Notes:
  - Query-string-bearing routes remain dynamic for now; any future normalized query support needs an explicit artifact-key contract.
  - The static path contract assumes artifacts live under a public directory tree that Apache can serve directly in later stages.

## Stage 2 - Add web-server bypass and dynamic fallback
- Changes:
  - Extended [`php_host/public/.htaccess`](/home/wsl/v2/php_host/public/.htaccess) with guarded rewrite rules that serve `_static_html/.../index.html` directly for allowlisted anonymous `GET` routes when the generated file exists.
  - Kept the guards conservative by requiring an empty query string and no `Authorization` or `Cookie` headers before static bypass can apply.
  - Added [`test_php_host_htaccess.py`](/home/wsl/v2/tests/test_php_host_htaccess.py) to lock the rewrite contract to the allowlisted route set and confirm PHP front-controller fallback remains the terminal rule.
- Verification:
  - Ran `python -m unittest tests.test_php_host_htaccess tests.test_php_host_cache.PhpHostCacheTests.test_static_html_request_only_allows_safe_anonymous_html_routes tests.test_php_host_cache.PhpHostCacheTests.test_static_html_public_path_maps_allowlisted_routes_to_index_files`
  - Result: 3 tests passed.
- Notes:
  - The direct static hit path now depends on artifacts being published under the public `_static_html/` tree.
  - Shared-host rewrite behavior still needs end-to-end validation once artifact generation lands.

## Stage 3 - Generate and invalidate canonical public HTML artifacts
- Changes:
  - Extended [`php_host/public/cache.php`](/home/wsl/v2/php_host/public/cache.php) with `forum_read_static_html()`, `forum_store_static_html(...)`, and `forum_clear_static_html()` so allowlisted public HTML can be materialized into `_static_html/`, reused, and invalidated.
  - Updated [`php_host/public/index.php`](/home/wsl/v2/php_host/public/index.php) to serve an existing static artifact before CGI work, store canonical Python-rendered HTML after successful allowlisted reads, and clear the static tree after successful mutating requests.
  - Expanded [`test_php_host_cache.py`](/home/wsl/v2/tests/test_php_host_cache.py) with end-to-end coverage for artifact creation, static-hit reuse, and write-trigger invalidation.
- Verification:
  - Ran `python -m unittest tests.test_php_host_cache.PhpHostCacheTests.test_php_host_caches_allowlisted_reads_and_marks_hit_headers tests.test_php_host_cache.PhpHostCacheTests.test_php_host_stores_and_reuses_static_html_for_allowlisted_reads tests.test_php_host_cache.PhpHostCacheTests.test_successful_write_clears_php_microcache`
  - Result: 3 tests passed.
- Notes:
  - The PHP fallback static-hit path is intentionally retained even though Apache should serve these files first in production; it keeps behavior correct when rewrite bypass is unavailable or untested locally.
  - Invalidation is coarse for now and clears the full `_static_html/` tree after successful writes.

## Stage 4 - Make the username CTA static-safe before first paint
- Changes:
  - Reworked the shared banner shell in [`forum_web/templates.py`](/home/wsl/v2/forum_web/templates.py) so pages emit a tiny head bootstrap that reads `forum_username_claim_cta` from local storage, hydrates that state from server-known eligibility when available, and applies first-paint CTA visibility through document-level attributes.
  - Added the shared CTA module to normal page renders and updated [`templates/assets/username_claim_cta.js`](/home/wsl/v2/templates/assets/username_claim_cta.js) to read, write, and apply stored CTA state instead of toggling a server-owned `hidden` attribute after load.
  - Updated [`templates/assets/site.css`](/home/wsl/v2/templates/assets/site.css) so the banner is hidden by default until the bootstrap marks it visible, and refreshed server/asset tests to match the new client-owned contract.
- Verification:
  - Ran `python -m unittest tests.test_account_setup_initial_render tests.test_board_index_page tests.test_compose_thread_page tests.test_profile_update_page tests.test_username_claim_cta_asset`
  - Result: 31 tests passed.
- Notes:
  - First-paint visibility now depends on browser-readable state; without local storage, the banner still falls back to hidden unless the current dynamic response can hydrate fresh eligibility into the bootstrap.
  - The profile page no longer embeds a static per-request CTA href for anonymous readers; the shared CTA link is now client-populated.
