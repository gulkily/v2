# Compose Reply Latency Reduction Step 1: Solution Assessment

## Problem Statement
Choose the best way to make `/compose/reply` fast in production while considering both a simpler Python path now and a full PHP implementation that no longer depends on Python components.

### Option A: Simplify the existing Python `/compose/reply` path
- Pros:
  - Smallest path to a measurable latency reduction.
  - Preserves the current write-flow architecture and avoids duplicating compose business rules immediately.
  - Directly targets the known waste: per-request startup checks, full repository loads, and global identity/moderation work for a single reply target.
- Cons:
  - Still leaves `/compose/reply` dependent on Python CGI on cache misses.
  - Does not deliver a PHP-only serving path.
  - May reduce but not eliminate cold-start and process-spawn costs.

### Option B: Build a full PHP-native `/compose/reply` implementation and remove Python dependencies for that route
- Pros:
  - Best long-term latency outcome because the route no longer requires Python execution.
  - Aligns with the broader PHP-native read strategy instead of treating compose reply as a permanent exception.
  - Can eliminate repeated Python startup, post-index checks, and full-state loading for this page.
- Cons:
  - Highest scope and parity risk because compose reply currently depends on Python-rendered context and business rules.
  - Requires defining PHP-owned data contracts for thread, parent post, moderation visibility, and compose-page rendering inputs.
  - Slower to deliver the first production improvement.

### Option C: Two-phase approach: simplify Python first, then replace it with a full PHP-native implementation
- Pros:
  - Delivers a smaller near-term fix while still targeting a Python-free end state.
  - Lets production measurements after the Python simplification guide the PHP scope and prove which data the route actually needs.
  - Reduces rewrite risk by shrinking the route’s data contract before mirroring it in PHP.
- Cons:
  - Requires two implementation cycles instead of one.
  - Some Python work will be transitional rather than final.
  - Needs discipline so the interim Python cleanup does not grow into a permanent half-solution.

## Recommendation
Recommend Option C: first simplify the Python `/compose/reply` path to remove obvious waste, then use the smaller contract to implement a full PHP-native route that no longer depends on Python components.

This matches the production evidence: the route is slow both because it misses the PHP fast path and because the Python handler does far more repository work than the page needs. Step 2 should define the minimal reply-compose read contract, the acceptable interim Python-only latency target, and the final PHP-native parity boundary.
