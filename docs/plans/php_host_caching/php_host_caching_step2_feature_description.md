## Problem
The PHP-primary host profile currently launches the canonical Python read surface on every public request, which makes repeated page loads unnecessarily slow on slower shared hosts. The next slice should reduce that repeated read cost without changing canonical Python rendering behavior or letting cached reads drift far from recent writes.

## User Stories
- As a visitor, I want repeated board, thread, and post views to load faster on the PHP-hosted deployment so that browsing feels responsive.
- As a deployer on a PHP-primary host, I want the optimization to stay inside the PHP adapter so that the canonical Python application and repository behavior remain unchanged.
- As an operator, I want recent writes to invalidate cached public reads so that newly created content appears promptly.
- As a maintainer, I want the cache scope to stay explicit and limited to safe read surfaces so that write endpoints and mutable workflows do not become stale.

## Core Requirements
- The slice must add PHP-side caching only for explicitly allowlisted safe `GET` routes in the PHP front controller.
- The slice must keep the canonical Python application as the source of truth for rendered bodies, status codes, and route semantics.
- The slice must leave write endpoints uncached and clear cached public reads after successful write operations routed through the PHP shim.
- The slice must add cache headers for canonical static asset routes without introducing a separate asset pipeline or changing asset URLs.
- The slice must avoid caching behavior for routes that depend on mutable form state, write submission bodies, or non-public request context.

## Shared Component Inventory
- Public read adapter: extend [`php_host/public/index.php`](/home/wsl/v2/php_host/public/index.php) as the only host-specific caching layer because it already bridges public requests into the canonical Python surface.
- Canonical read surface: reuse [`cgi-bin/forum_web.py`](/home/wsl/v2/cgi-bin/forum_web.py) and [`forum_web/web.py`](/home/wsl/v2/forum_web/web.py) unchanged for page rendering, read APIs, and asset bodies.
- Canonical write surfaces: reuse existing write endpoints such as `/api/create_thread` and `/api/create_reply`; this feature does not replace or reinterpret their behavior.
- Deployment documentation: extend [`docs/php_primary_host_installation.md`](/home/wsl/v2/docs/php_primary_host_installation.md) to describe any writable cache location and operator-facing cache expectations.
- New UI/API surfaces: none; this slice improves host-side delivery of existing routes only.

## Simple User Flow
1. A visitor requests an allowlisted public read route through the PHP front controller.
2. The PHP adapter checks for a fresh cached response for that route.
3. If no fresh cache entry exists, the adapter forwards the request to the canonical Python surface and stores the returned read response for a short period.
4. The visitor receives the canonical response body, while static asset routes also receive explicit cache headers.
5. After a successful write through the PHP shim, the adapter clears cached public reads so later visitors fetch fresh content.

## Success Criteria
- Repeated requests to allowlisted public read routes can be served from the PHP layer for a short interval without changing response shape or canonical rendering output.
- Successful writes through the PHP shim cause cached public reads to be cleared before the next read is served.
- Static asset responses on the PHP-hosted deployment include explicit cache headers.
- Write endpoints, compose flows, and other non-allowlisted routes remain uncached.
- The deployment model remains PHP adapter plus canonical Python application, with no new browser pages, API contracts, or duplicated rendering logic.
