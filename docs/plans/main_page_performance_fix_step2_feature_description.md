# Main Page Performance Fix Step 2: Feature Description

## Problem
Main public pages such as `/` and `/threads/...` are still loading slowly in production because ordinary browsing is missing the intended cheap public read path and falling back to expensive Python CGI work. The next slice should restore fast public reads, reduce avoidable read-time index work, and leave room for a small expansion of PHP-native reads where that clearly improves hot public routes.

## User Stories
- As a reader, I want `/` and thread pages to load quickly during normal browsing so that the forum feels responsive.
- As a participating reader, I want harmless identity-hint cookies to avoid breaking public fast paths so that ordinary browsing does not become slower after setup flows.
- As an operator, I want the main public routes to stay off the slow-operations list in steady state so that production latency regressions are easier to spot.
- As a maintainer, I want any expanded PHP-native read surface to stay narrowly scoped to hot public routes so that performance improves without uncontrolled duplication.

## Core Requirements
- Anonymous and cache-safe public reads for `/` and `/threads/...` must use the intended native/static/public fast path whenever supporting artifacts exist.
- Ordinary public reads must not pay avoidable startup-style post-index work during steady-state CGI serving.
- The feature must preserve the current public route shapes, moderation behavior, and write authority boundaries.
- The feature may extend PHP-native reads only to a small, explicitly bounded set of hot public routes that fit the same public-read contract.
- The existing slow-operations surface must remain the canonical place to confirm whether main public routes are still slow.

## Shared Component Inventory
- PHP host route gating in `php_host/public/index.php`: extend the canonical fast-path eligibility logic rather than creating a second public routing layer.
- Public cache and cookie-safety rules in `php_host/public/cache.php`: reuse and refine the existing cache-safety contract rather than inventing a separate cookie policy for native reads.
- Python request routing and startup/readiness behavior in `forum_web/web.py`: extend the existing request path rather than adding alternate Python endpoints.
- Post-index readiness and refresh behavior in `forum_core/post_index.py`: reuse the current derived-index authority rather than introducing a second read-state system.
- Existing PHP-native read artifacts in `forum_core/php_native_reads.py` and current static HTML artifacts: extend these canonical public-read surfaces rather than building a separate rendering stack.
- Existing response-header and slow-operation surfaces in the PHP host and `forum_core/operation_events.py`: reuse these for verification rather than adding a separate monitoring feature.

## Simple User Flow
1. A reader opens `/` or `/threads/<id>` in normal browsing, including after identity-hint setup.
2. The request stays on the public fast path when the request is still cache-safe and artifacts are available.
3. If a route is still slow, the operator can confirm that in the existing slow-operations surface and distinguish it from expected heavier routes.
4. If a small number of additional hot public routes still justify it, the same public-read strategy can be extended to them without changing the write path.

## Success Criteria
- `/` and warmed `/threads/...` requests normally resolve through the intended public fast path instead of appearing regularly in slow Python request records.
- Browsing with only the identity-hint cookie does not force `/` and `/threads/...` off the public fast path.
- Ordinary steady-state public reads no longer trigger repeated expensive startup-style post-index work.
- The scope of any added PHP-native route remains explicitly limited to hot public reads that follow the same safety model.
- Production verification shows the main public pages are no longer common entries in `/operations/slow/`, leaving heavier routes such as `/activity/` easier to isolate.
