## Problem
The production site is currently served through Apache and the PHP shim, which buffers the full CGI response before sending it. When a request-triggered post-index rebuild happens on that path, users experience a long stall instead of immediate feedback, so the next slice should provide a PHP-compatible status experience without depending on true streaming.

## User Stories
- As a reader on the public PHP-hosted site, I want an immediate status page when a request must wait on reindexing so that the site feels active rather than frozen.
- As a reader, I want the status page to explain that forum data is being refreshed so that I understand why the requested page is delayed.
- As an operator, I want rebuild-triggered waits on the PHP path to remain visible through the existing logs and status signals so that the delay is diagnosable.
- As a maintainer, I want the PHP host to stay an adapter around the canonical Python application so that this feature does not create a second rendering model.

## Core Requirements
- The PHP-served public read path must be able to return an immediate user-facing status response when a request-triggered post-index rebuild is needed.
- The status response must work correctly on the buffered Apache -> PHP -> CGI path without relying on incremental response streaming.
- The feature must preserve the canonical Python read surface and post-index lifecycle as the source of truth for rebuild detection and final page rendering.
- The covered indexed-read routes must resume normal rendering automatically or predictably once the index is ready, without exposing raw internal diagnostics to readers.
- Existing rebuild logging and operational visibility must remain the operator-facing diagnosis path for the same work.

## Shared Component Inventory
- PHP front controller: extend [php_host/public/index.php](/home/wsl/v2/php_host/public/index.php) as the public host adapter because this is the confirmed production entrypoint and the place where buffered response behavior must be handled explicitly.
- CGI bridge: reuse [forum_cgi/wsgi_gateway.py](/home/wsl/v2/forum_cgi/wsgi_gateway.py) as the current buffered Python bridge; this slice should work with that boundary rather than pretending it streams.
- Canonical web application: reuse [forum_web/web.py](/home/wsl/v2/forum_web/web.py) for rebuild detection, status semantics, and final page rendering so the PHP layer does not invent a parallel read model.
- Post-index lifecycle: reuse [forum_core/post_index.py](/home/wsl/v2/forum_core/post_index.py) as the canonical source of truth for stale-index detection and rebuild behavior.
- Existing operator-facing logging: reuse current rebuild logs and related operation visibility rather than creating a separate diagnostics surface for PHP-hosted waits.

## Simple User Flow
1. A reader requests `/`, a thread, or another covered indexed-read page through the PHP-hosted public site.
2. The system determines that the post index must be rebuilt before the requested page can render normally.
3. The reader receives an immediate status page explaining that forum data is being refreshed.
4. Follow-up requests continue to show the status experience until the rebuild completes.
5. Once the index is ready, the reader is returned to the normal requested page flow.

## Success Criteria
- Covered reindex-triggered reads on the public PHP-hosted site no longer appear as a blank or stalled page load.
- Readers receive a clear, intentional status response that explains the forum is refreshing data.
- The feature works on the buffered Apache/PHP/CGI production path without depending on streaming semantics that path cannot provide.
- Canonical rebuild detection and final page rendering remain owned by the existing Python application and post-index lifecycle.
