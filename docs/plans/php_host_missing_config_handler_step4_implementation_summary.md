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

## Stage 2 - add polished missing-config diagnostic page
- Changes:
  - Upgraded the missing-config helper in [index.php](/home/wsl/v2/php_host/public/index.php) from raw plain text to a deliberate HTML diagnostic page.
  - Added lightweight inline styling, a clear title, the missing include name, the expected path, the primary `./forum php-host-setup` recovery command, and copy that distinguishes deployment failure from application failure.
  - Preserved explicit failure semantics: the page still returns HTTP `500` and stops request handling when the real config include is absent.
- Verification:
  - Ran `php -l php_host/public/index.php`.
  - Ran the temp-copy CGI smoke test with no config present and confirmed:
    - `Status: 500 Internal Server Error`
    - `Content-Type: text/html; charset=utf-8`
    - HTML output with `<title>PHP host setup required</title>`
    - visible recovery guidance including `./forum php-host-setup /absolute/path/to/public-web-root`
- Notes:
  - The page styling stays fully local to the PHP adapter so this stage does not introduce a broader shared presentation layer.

## Stage 3 - link the page back to the install guide
- Changes:
  - Added one explicit documentation-reference card to the missing-config page in [index.php](/home/wsl/v2/php_host/public/index.php).
  - Pointed operators to `docs/php_primary_host_installation.md` in the application checkout as the canonical long-form recovery guide, while keeping `./forum php-host-setup` as the primary action.
- Verification:
  - Ran `php -l php_host/public/index.php`.
  - Ran the temp-copy CGI smoke test and confirmed the rendered page includes:
    - `Need more detail?`
    - `docs/php_primary_host_installation.md`
    - the existing `./forum php-host-setup /absolute/path/to/public-web-root` recovery command
- Notes:
  - The docs reference is textual rather than an external link so it still works in broken local deployments without depending on public documentation hosting.

## Stage 4 - regression coverage for missing-config rendering
- Changes:
  - Added focused PHP-host coverage in [test_php_host_missing_config_page.py](/home/wsl/v2/tests/test_php_host_missing_config_page.py) for the missing `forum_host_config.php` case.
  - The test exercises a temp-copy PHP CGI request with no config present and asserts the stable operator-facing contract: HTTP `500`, HTML content type, page title, missing include name, expected path, primary recovery command, and docs reference.
- Verification:
  - Ran `python3 -m unittest tests.test_php_host_missing_config_page`.
  - Ran `php -l php_host/public/index.php`.
- Notes:
  - The assertions target durable operator-facing cues rather than the entire HTML body so future copy/layout adjustments remain possible without losing coverage for the recovery contract.
