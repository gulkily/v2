## Stage 1
- Goal: Define one canonical Python-side contract for rebuild-required reads that the PHP host can recognize without rendering the final destination page.
- Dependencies: Approved Step 2; existing indexed-read readiness checks in `forum_core/post_index.py`; current request dispatch in `forum_web/web.py`.
- Expected changes: conceptually extend the canonical web application so covered indexed-read requests can produce an explicit rebuild-status response shape for buffered hosts; planned seams may include a helper such as `maybe_build_post_index_rebuild_status_response(environ, start_response, ...)` or an equivalent status/header contract that distinguishes "show status page now" from "render final page now."
- Verification approach: manual smoke check against the canonical Python app with a missing or stale index to confirm covered requests enter the rebuild-status path instead of going straight to the final page render.
- Risks or open questions:
  - Need a contract the PHP layer can detect without duplicating rebuild logic.
  - Need to keep normal non-rebuild reads and write endpoints unaffected.
- Canonical components/API contracts touched: `forum_web/web.py` request dispatch contract; `forum_core/post_index.py` readiness lifecycle.

## Stage 2
- Goal: Make the Apache/PHP production path return an immediate rebuild status page and hand users back to the canonical read flow once the index is ready.
- Dependencies: Stage 1; public adapter in `php_host/public/index.php`; buffered CGI bridge in `forum_cgi/wsgi_gateway.py`.
- Expected changes: conceptually extend the PHP front controller so it detects the canonical rebuild-status response and serves a lightweight user-facing page immediately on covered indexed-read routes; planned seams may include a PHP-side status renderer and a predictable follow-up strategy such as timed refreshes back to the original URL while rebuild work proceeds through the existing canonical path.
- Verification approach: manual smoke check on the PHP-hosted path after removing `state/cache/post_index.sqlite3` to confirm `/` returns the status page immediately and eventually resumes normal rendering.
- Risks or open questions:
  - Need to ensure follow-up requests do not trap users in a permanent status loop once the index is ready.
  - Need to keep the PHP cache layer from storing temporary rebuild-status responses incorrectly.
- Canonical components/API contracts touched: `php_host/public/index.php`; `forum_cgi/wsgi_gateway.py`; Python rebuild-status response contract from Stage 1.

## Stage 3
- Goal: Add regression coverage for the canonical rebuild-status contract and the buffered PHP-hosted user flow.
- Dependencies: Stages 1-2; existing PHP-host tests, startup tests, and gateway tests.
- Expected changes: extend automated tests to cover covered indexed-read requests that require rebuilds on the PHP-hosted path, including cold-start behavior and the transition back to normal rendering; likely touch startup tests, PHP host cache/adapter tests, and gateway tests without changing storage models.
- Verification approach: run targeted automated suites for startup behavior, PHP host behavior, and indexed-read routes; manual smoke check on a PHP-hosted request path after forcing a rebuild.
- Risks or open questions:
  - Test fixtures may need to model "status page now, normal page later" without depending on exact copy or timing.
  - Need to keep assertions focused on contract and route behavior rather than implementation-specific buffering details.
- Canonical components/API contracts touched: `tests/test_post_index_startup.py`, `tests/test_php_host_cache.py`, route-level page tests, and gateway/adapter coverage around the PHP host path.
