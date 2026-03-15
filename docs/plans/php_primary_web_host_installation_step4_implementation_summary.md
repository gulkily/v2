## Stage 1 - Supported host profile
- Changes:
  - Added [php_primary_host_installation.md](/home/wsl/v2/docs/php_primary_host_installation.md) defining the supported PHP-primary hosting profile, unsupported environments, canonical Python boundary, planned deployment layout, and the minimal PHP adapter contract.
- Verification:
  - Reviewed the documented host requirements against the current canonical entrypoints in `forum_read_only/web.py`, `cgi-bin/create_thread.py`, and `cgi-bin/create_reply.py`.
  - Confirmed the profile stays narrow: PHP front controller plus `.htaccess` for public routing, with Python remaining the canonical read/write implementation.
- Notes:
  - The remaining implementation work depends on picking one thin request-forwarding strategy that a typical Apache shared host can support without turning this into a PHP rewrite.

## Stage 2 - PHP read adapter and routing
- Changes:
  - Added [forum_web.py](/home/wsl/v2/cgi-bin/forum_web.py) as a CGI bridge that exposes the existing WSGI application through CGI output.
  - Added [wsgi_gateway.py](/home/wsl/v2/forum_cgi/wsgi_gateway.py) to translate CGI request state into a WSGI environ and serialize the application's response back to CGI.
  - Added sample PHP-host public entry files at [index.php](/home/wsl/v2/php_host/public/index.php) and [.htaccess](/home/wsl/v2/php_host/public/.htaccess) so Apache can route public requests through a thin PHP front controller.
  - Extended [php_primary_host_installation.md](/home/wsl/v2/docs/php_primary_host_installation.md) to reference the concrete sample adapter files.
- Verification:
  - Ran `REQUEST_METHOD=GET PATH_INFO=/ QUERY_STRING= SERVER_NAME=localhost SERVER_PORT=80 SERVER_PROTOCOL=HTTP/1.1 python3 cgi-bin/forum_web.py` and confirmed a `Status: 200 OK` HTML response for the board index.
  - Ran `REQUEST_METHOD=GET PATH_INFO=/assets/site.css QUERY_STRING= SERVER_NAME=localhost SERVER_PORT=80 SERVER_PROTOCOL=HTTP/1.1 python3 cgi-bin/forum_web.py` and confirmed a `Status: 200 OK` CSS response for the canonical asset path.
  - Ran `REQUEST_METHOD=GET REQUEST_URI=/ QUERY_STRING= SERVER_NAME=localhost SERVER_PORT=80 SERVER_PROTOCOL=HTTP/1.1 php php_host/public/index.php` and confirmed the PHP shim returned the board index HTML.
  - Ran `REQUEST_METHOD=GET REQUEST_URI=/threads/T01 QUERY_STRING= SERVER_NAME=localhost SERVER_PORT=80 SERVER_PROTOCOL=HTTP/1.1 php php_host/public/index.php` and confirmed the PHP shim returned an existing thread page.
  - Ran `REQUEST_METHOD=GET REQUEST_URI=/assets/site.css QUERY_STRING= SERVER_NAME=localhost SERVER_PORT=80 SERVER_PROTOCOL=HTTP/1.1 php php_host/public/index.php` and confirmed the PHP shim returned CSS content for the asset route.
- Notes:
  - The PHP shim currently shells out to the Python CGI bridge for each request, which keeps the adapter thin but makes host capability requirements explicit.

## Stage 3 - Canonical write paths through the PHP shim
- Changes:
  - Updated [index.php](/home/wsl/v2/php_host/public/index.php) so the adapter uses `FORUM_PHP_APP_ROOT` for locating deployed application code and preserves the existing meaning of `FORUM_REPO_ROOT` as the forum data repository root.
  - Updated [index.php](/home/wsl/v2/php_host/public/index.php) to read request bodies from `php://stdin` when verified through CLI-style execution, keeping hosted `POST` request forwarding intact for the adapter smoke harness.
  - Extended [php_primary_host_installation.md](/home/wsl/v2/docs/php_primary_host_installation.md) to document the app-root override and to state explicitly that browser compose and API writes remain on `/api/create_thread` and `/api/create_reply`.
- Verification:
  - Ran a disposable hosted-path harness that generated an OpenPGP keypair, signed a thread payload, and submitted `POST /api/create_thread` through `php_host/public/index.php` with `FORUM_PHP_APP_ROOT=/home/wsl/v2` and `FORUM_REPO_ROOT=<temp repo>`; confirmed a stored thread record, signature/public-key sidecars, identity bootstrap record, and git commit `create_thread: php-host-thread-001`.
  - Ran the same hosted-path harness for `POST /api/create_reply`; confirmed a stored reply record plus git commit `create_reply: php-host-reply-001`.
  - Requested `GET /compose/thread` through the PHP shim and confirmed the rendered page still points at `/api/create_thread`.
- Notes:
  - The write smoke harness reports the current auto-reply failure path when no Dedalus connectivity is available, but the root thread write still succeeds and remains committed as expected.
