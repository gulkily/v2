## Stage 1 - Extract cache policy helpers
- Changes:
  - Added [cache.php](/home/wsl/v2/php_host/public/cache.php) to hold the PHP-host cache policy, allowlisted read-route detection, cache-path helpers, microcache persistence, and static-asset cache headers.
  - Slimmed [index.php](/home/wsl/v2/php_host/public/index.php) back down to a thin front controller that requires the cache helper, checks for a cached read hit, and stores successful allowlisted read responses without moving canonical rendering logic out of Python.
- Verification:
  - Ran `php -l php_host/public/cache.php` and `php -l php_host/public/index.php`; both passed.
  - Ran `FORUM_PHP_CACHE_DIR=<temp>/cache REQUEST_METHOD=GET REQUEST_URI=/ QUERY_STRING= SERVER_NAME=localhost SERVER_PORT=80 SERVER_PROTOCOL=HTTP/1.1 php php_host/public/index.php` and confirmed a cache file was created for the board index route.
  - Ran `FORUM_PHP_CACHE_DIR=<temp>/cache REQUEST_METHOD=GET REQUEST_URI=/assets/site.css QUERY_STRING= SERVER_NAME=localhost SERVER_PORT=80 SERVER_PROTOCOL=HTTP/1.1 php php_host/public/index.php` and confirmed no microcache file was created for the asset route.
- Notes:
  - Stage 1 keeps the write-path invalidation work out of the committed scope; that will be finished in Stage 2.

## Stage 2 - Add cache invalidation and focused coverage
- Changes:
  - Extended [cache.php](/home/wsl/v2/php_host/public/cache.php) with mutating-request detection and full microcache-directory clearing so successful write requests invalidate cached public reads.
  - Updated [index.php](/home/wsl/v2/php_host/public/index.php) to clear the PHP microcache after successful non-`GET`/`HEAD` responses while leaving write responses themselves uncached.
  - Added [test_php_host_cache.py](/home/wsl/v2/tests/test_php_host_cache.py) covering cache miss/hit headers for allowlisted reads, asset cache headers without asset microcaching, and cache invalidation after a successful `POST /api/create_thread` through the real `php-cgi` entrypoint.
- Verification:
  - Ran `python3 -m unittest tests.test_php_host_cache`; passed all 3 tests.
  - Re-ran `php -l php_host/public/cache.php` and `php -l php_host/public/index.php`; both passed.
- Notes:
  - The focused test uses `php-cgi` instead of a local PHP server because that path exposes real CGI headers without requiring a long-lived listening socket in this environment.

## Stage 3 - Document operator cache behavior
- Changes:
  - Extended [php_primary_host_installation.md](/home/wsl/v2/docs/php_primary_host_installation.md) with the PHP microcache boundary, writable cache directory and TTL settings, and post-install checks for cache hits, asset cache headers, and write-triggered invalidation.
- Verification:
  - Ran `python3 -m unittest tests.test_php_host_cache`; passed all 3 tests after the documentation update.
  - Reviewed the updated installation guide to confirm it documents `FORUM_PHP_CACHE_DIR`, `FORUM_PHP_MICROCACHE_TTL`, the narrow allowlist boundary, and the expected post-install smoke checks.
- Notes:
  - The documented cache TTL stays intentionally short to minimize drift between cached reads and recent writes on slower PHP-primary hosts.
