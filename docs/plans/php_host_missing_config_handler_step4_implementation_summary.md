## Stage 1 - isolate missing-config response contract
- Changes:
  - Added a dedicated PHP helper in [index.php](/home/wsl/v2/php_host/public/index.php) to render the missing `forum_host_config.php` failure instead of inlining the response directly inside `forum_host_config()`.
  - Kept the current failure semantics unchanged for this stage: HTTP `500`, `text/plain`, explicit missing-config output, and immediate exit behavior.
- Verification:
  - Ran `php -l php_host/public/index.php`.
  - Ran a temp-copy CGI smoke test with no config present:
    `tmpdir=$(mktemp -d) && mkdir -p "$tmpdir/public" && cp php_host/public/index.php php_host/public/cache.php "$tmpdir/public/" && REDIRECT_STATUS=200 REQUEST_METHOD=GET SCRIPT_FILENAME="$tmpdir/public/index.php" REQUEST_URI=/ php-cgi -q "$tmpdir/public/index.php"`
  - Confirmed the response still returns `Status: 500 Internal Server Error` plus:
    - `Missing PHP host config include.`
    - `Expected: /tmp/.../public/forum_host_config.php`
- Notes:
  - This stage intentionally does not improve presentation yet; it only creates the canonical response boundary required for later stages.
