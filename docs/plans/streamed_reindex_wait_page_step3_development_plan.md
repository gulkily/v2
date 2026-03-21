## Stage 1
- Goal: Add one canonical streamed-response path for covered reindex waits on the long-lived Python host.
- Dependencies: Approved Step 2; current WSGI entrypoint in `forum_web/web.py`; existing post-index readiness and rebuild flow in `forum_core/post_index.py`.
- Expected changes: conceptually extend the Python application path so selected GET routes can return an iterable response that sends a minimal waiting shell before the rebuild completes and then finishes the same request lifecycle; planned contracts may include a streamed-response helper such as `render_streamed_reindex_wait_response(...)` and a small request-capability decision based on the active WSGI environment.
- Verification approach: manual smoke check on the long-lived Python server with a forced stale or missing index to confirm the waiting shell paints before rebuild completion and the request still completes successfully.
- Risks or open questions:
  - Need to ensure headers are sent exactly once before yielding body chunks.
  - Need to avoid breaking normal non-streamed routes or request-operation accounting.
- Canonical components/API contracts touched: `forum_web/web.py` WSGI application contract; `forum_core/post_index.py` readiness and rebuild lifecycle.

## Stage 2
- Goal: Keep CGI/PHP behavior explicit and correct while the streamed path lands only on the Python server.
- Dependencies: Stage 1; CGI buffering gateway in `forum_cgi/wsgi_gateway.py`; PHP shim bridge in `php_host/public/index.php`.
- Expected changes: conceptually gate the streamed wait behavior to environments that can actually deliver early body bytes; keep the current CGI/PHP path on a documented non-streaming fallback without pretending it streams today; planned seams may include a helper like `request_supports_streaming(environ) -> bool` keyed off existing WSGI runtime metadata.
- Verification approach: manual smoke check that CGI/PHP-compatible request paths still return correct full responses and do not enter the streamed branch; targeted automated tests around the gateway and request capability decision.
- Risks or open questions:
  - Need a crisp runtime rule that is easy to reason about and test.
  - Need to avoid introducing partial streaming semantics into the CGI gateway before that layer is explicitly redesigned.
- Canonical components/API contracts touched: `forum_cgi/wsgi_gateway.py`; `php_host/public/index.php`; Python request capability logic in `forum_web/web.py`.

## Stage 3
- Goal: Lock the streamed Python behavior and the CGI/PHP fallback boundary into regression coverage.
- Dependencies: Stages 1-2; existing startup, board-index, and WSGI gateway tests.
- Expected changes: extend request tests to cover cold-start and stale-index streamed waits on the Python path, plus explicit non-streaming expectations for the CGI gateway; likely touch startup tests, board-index tests, and WSGI gateway tests without changing storage models.
- Verification approach: run targeted automated suites for startup behavior, indexed read routes, and the CGI gateway; manual smoke check on the long-lived Python server after removing `state/cache/post_index.sqlite3`.
- Risks or open questions:
  - Test fixtures may need to distinguish “iterable response available” from “fully buffered CGI response” without becoming brittle.
  - Need to keep assertions focused on behavior rather than exact copy or chunk boundaries.
- Canonical components/API contracts touched: `tests/test_post_index_startup.py`, route-level page tests, and `tests/test_wsgi_gateway.py`.
