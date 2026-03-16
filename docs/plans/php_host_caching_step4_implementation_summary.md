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
