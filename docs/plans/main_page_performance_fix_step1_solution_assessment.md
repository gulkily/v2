# Main Page Performance Fix Step 1: Solution Assessment

## Problem Statement
Choose the smallest coherent way to make main public pages fast again without creating a fragile second application path.

### Option A: Rely mostly on longer TTL caching and deploy warmup
- Pros:
  - Smallest immediate change.
  - Low implementation risk.
  - Can improve repeat traffic quickly.
- Cons:
  - Does not fix why normal browsing misses the fast path.
  - Leaves cold requests and stale-index reads expensive.
  - Risks hiding correctness and routing problems behind cache duration.

### Option B: Restore and harden the intended public fast path for main pages
- Pros:
  - Directly targets the observed problem that `/` and `/threads/...` are falling through to Python.
  - Preserves the current architecture: PHP/static/native for safe public reads, Python for writes and heavier routes.
  - Reduces both latency and Python CGI pressure without broad duplication.
- Cons:
  - Requires careful boundary rules around cookies, startup checks, and artifact freshness.
  - May still leave `/activity/` as a separate performance problem.

### Option C: Extend PHP-native reads to a small additional set of hot public routes
- Pros:
  - Builds on the same fast-path strategy instead of introducing a separate performance mechanism.
  - Can reduce Python usage further for a few clearly hot public pages.
  - Gives room to cover routes that remain slow after the current fast path is fixed.
- Cons:
  - Increases duplicate rendering and artifact-maintenance scope.
  - Needs strict limits so the PHP-native surface does not expand faster than its shared data contracts.
  - Raises regression risk if additional routes depend on identity or moderation details that are harder to mirror safely.

## Recommendation
Recommend a combined B+C approach: restore and harden the intended public fast path first, then extend PHP-native reads only to a small additional set of hot public routes if they still matter after re-measurement.

This keeps the first move tightly aligned with the production evidence while leaving room for selective expansion instead of treating the current native surface as fixed. Step 2 should focus on fast-path eligibility, CGI-safe index readiness behavior, observability for slow reads, deployment verification, and strict criteria for any added PHP-native routes.
