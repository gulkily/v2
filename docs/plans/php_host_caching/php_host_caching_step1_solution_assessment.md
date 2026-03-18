## Problem Statement
Choose the smallest useful way to improve page-load speed on a slower PHP-primary host without changing the canonical Python application behavior or making cached reads drift too far from recent writes.

### Option A: Add PHP-side file microcaching for safe GET routes plus cache headers for static assets
- Pros:
  - Targets the actual hot path on the host: repeated PHP-to-Python CGI execution for public reads.
  - Can speed up `/`, thread pages, post pages, `/instance/`, `/llms.txt`, and selected read APIs without changing the canonical Python app.
  - Keeps write behavior uncached and can clear cached reads after successful writes.
  - Works even when the Python app is still launched per request through the current shim.
- Cons:
  - Needs careful route allowlisting and invalidation rules.
  - Adds deployment-state files that must live somewhere writable on the host.
  - Risks brief staleness if TTLs or invalidation are wrong.

### Option B: Add caching only inside the Python application layer
- Pros:
  - Keeps caching logic closer to the canonical renderer.
  - Could simplify later non-PHP deployments if a persistent Python process is introduced.
- Cons:
  - Helps little on the current shared-host path because each CGI request starts a fresh Python process.
  - Does not avoid the PHP-to-Python process startup cost that appears to dominate current read latency.
  - Risks spending time on caches that do not materially improve the deployed experience.

### Option C: Use documentation-only guidance to rely on Apache/browser asset caching and leave dynamic pages uncached
- Pros:
  - Smallest implementation change.
  - Static assets would become cheaper immediately.
  - Very low correctness risk.
- Cons:
  - Leaves the expensive dynamic page path unchanged.
  - Does not materially improve repeated visits to thread pages, index pages, or other Python-rendered reads.
  - Puts most of the performance problem outside the product instead of addressing it directly.

## Recommendation
Recommend Option A: add PHP-side file microcaching for safe GET routes plus cache headers for static assets.

This is the smallest coherent optimization for the current deployment model. The next steps should stay strict: cache only explicitly safe read routes, keep write endpoints uncached, clear read caches after successful writes, and avoid moving forum semantics or rendering logic out of the canonical Python application.
