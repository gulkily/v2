# On-Demand Static HTML For Public Reads Step 1: Solution Assessment

## Problem Statement
Choose the smallest coherent way, in PHP-shim mode, to let safe public read pages bypass PHP entirely by serving pre-generated HTML whenever possible.

### Option A: Web-server static-file bypass for allowlisted anonymous read routes
- Pros:
  - Matches the goal directly: repeated anonymous hits can skip PHP entirely and be served as static files.
  - Keeps the current app as the canonical renderer because files are generated from existing routes only when needed.
  - Limits the blast radius by restricting bypass behavior to explicitly safe public pages.
  - Gives a clearer traffic win than a PHP-side cache because the hot path becomes web-server file serving.
- Cons:
  - Needs rewrite or equivalent web-server rules plus a deterministic artifact layout.
  - Requires precise invalidation when posts, profiles, or moderation-visible state change.
  - Conflicts with any route whose output depends on cookies, session state, request headers, query variants, or per-request tokens.

### Option B: PHP-shim decides whether to serve a generated HTML artifact
- Pros:
  - Preserves a single entry path and avoids web-server-specific bypass rules.
  - Can reuse existing PHP routing and request inspection before falling back to a stored artifact.
  - Makes it easier to gate static serving on app-level safety checks.
- Cons:
  - Does not satisfy the full goal of bypassing PHP whenever possible because every request still enters the shim.
  - Leaves more burst load on PHP than direct static-file serving.
  - Can blur the boundary between request-safe routes and dynamic routes instead of enforcing it at the edge.

### Option C: Longer-lived PHP public microcache
- Pros:
  - Smallest change to the current hosting path.
  - Preserves current route flow and cache-clearing behavior.
  - Could reduce repeated anonymous read pressure quickly.
- Cons:
  - Still depends on request-time PHP execution.
  - A TTL cache does not match the requirement to serve pre-generated files directly whenever safe.
  - Cache freshness is harder to reason about for selectively invalidated read pages.

## Conflicts To Resolve
- Authenticated, session-aware, or cookie-dependent pages cannot be safely bypassed.
- Pages with CSRF tokens, flash state, request diagnostics, or other per-request values cannot be frozen as shared HTML.
- Any read route whose output varies by permissions, moderation visibility, headers, host, scheme, or query-string must stay dynamic unless normalized explicitly.
- Compose, signed-write, and other mutation routes must always bypass static serving.
- Invalidation must cover post edits, profile changes, moderation state changes, and route alias changes so stale files do not outlive source data.

## Recommendation
Recommend Option A: web-server static-file bypass for allowlisted anonymous read routes in PHP-shim mode.

It is the smallest option that actually meets the requirement. It keeps dynamic behavior where needed, gives the largest traffic relief in shim deployments, and makes the conflict boundary explicit instead of hiding it inside PHP.
