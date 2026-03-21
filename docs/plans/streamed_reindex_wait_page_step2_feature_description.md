## Problem
When reindexing is triggered during a normal read request, users should see immediate feedback instead of a blank stall. The next slice should improve that experience through same-request streaming where the runtime supports it, while keeping the CGI/PHP path explicitly non-streaming until its buffering gateway is redesigned.

## User Stories
- As a reader on the long-lived Python host, I want the page to show a waiting state immediately when reindexing starts so that the request feels active rather than frozen.
- As a reader, I want the waiting state to explain that forum data is being refreshed so that I understand why the final page is delayed.
- As an operator, I want reindex-triggered waits to remain visible in the existing operation logs so that streamed feedback still maps to diagnosable backend work.
- As a maintainer, I want the feature to respect runtime boundaries so that the Python server and CGI/PHP shim do not pretend to support the same delivery model when they do not.

## Core Requirements
- The long-lived Python request path must be able to send a minimal waiting page before the index rebuild completes.
- The waiting experience must stay inside the same request lifecycle rather than depending on a separate background process.
- The feature must cover the canonical indexed-read pages where rebuild-triggered waits are currently felt most often.
- The CGI/PHP path must remain correct and explicit about its non-streaming behavior rather than advertising a streamed experience it cannot deliver through the current buffering gateway.
- Existing recent-operation and rebuild logging must remain the operator-facing diagnosis path for the same work.

## Shared Component Inventory
- Main WSGI request path in `forum_web/web.py`: extend the canonical Python application entry and covered read routes because this is where same-request streaming is feasible today.
- Indexed readiness and rebuild lifecycle in `forum_core/post_index.py`: reuse the current stale-index detection and rebuild path rather than inventing a second indexing model.
- CGI gateway in `forum_cgi/wsgi_gateway.py`: treat the current buffered CGI response path as the canonical reason streaming is unavailable under CGI/PHP, and document that it remains a fallback boundary for this slice.
- PHP shim in `php_host/public/index.php`: preserve the current CGI bridge contract rather than adding process-lifecycle tricks inside PHP for this feature.
- Existing rebuild and slow-operation logging: reuse the current logs and operation-events model as the canonical operator-facing source of truth.

## Simple User Flow
1. A reader opens `/`, a thread, or a profile page on the long-lived Python host.
2. The system detects that the post index needs rebuilding.
3. The request sends a minimal waiting page immediately and continues the rebuild inside the same request.
4. Once the rebuild completes, the final page content becomes available through the normal read flow.
5. On CGI/PHP, the system keeps the current non-streaming fallback behavior until that response pipeline is redesigned.

## Success Criteria
- On the long-lived Python host, covered reindex-triggered reads show visible feedback immediately rather than only after most of the rebuild has already elapsed.
- The waiting page clearly communicates that forum data is being refreshed within the current request.
- The feature does not depend on detached background work.
- The Python-server behavior and CGI/PHP behavior are intentionally differentiated and documented rather than conflated.
