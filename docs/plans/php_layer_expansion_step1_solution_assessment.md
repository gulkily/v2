# Step 1 – Solution Assessment: PHP Layer Expansion Strategy

## Problem Summary

The PHP native reads implementation successfully eliminated per-request Python execution for the board index (`/`), but three additional high-value read routes still incur full Python spawning:

1. **Thread detail pages** (`/threads/{id}`) – frequently accessed, most time-sensitive for reads
2. **Profile pages** (`/profiles/{slug}`) – lower traffic but personalization-limited (can be anonymous-read-cached)
3. **Post detail pages** (`/posts/{id}`) – moderate traffic, similar model to threads

Currently, every cache miss on these routes spawns a Python process (~50–500ms latency). The existing pattern (shared contract → prepared snapshot → PHP renderer) has already proven reliable for the board index.

## Proposed Expansion Approaches

### Option A: Threads First, Sequential Expansion
**Approach**: Extend the established 4-stage pattern to `/threads/{id}` next, then `/profiles/`, then `/posts/` in separate cycles.

**Pros**:
- Proven pattern (same methodology as board index)
- Each route is a complete, testable unit of work
- Lowest risk (incremental, reversible)
- Thread pages are the most frequently accessed after board index
- Easy to measure impact per route

**Cons**:
- Slower overall adoption (3+ separate planning/implementation cycles)
- Requires explicit invalidation coverage for all thread-affecting writes (posts, moderation, title updates, identity/profile display changes)
- Needs operator visibility into fallback frequency so missing/stale snapshot problems are detectable early

**Effort**: Medium per route (12-20 hours each), ~40-60 hours total

---

### Option B: Profile + Thread Hybrid
**Approach**: Implement thread detail AND profile pages simultaneously (same cycle) by recognizing they share common infrastructure (user/author display, moderation visibility).

**Pros**:
- Faster path to covering ~80% of traffic (threads + profiles combined)
- Shared contract logic for both (e.g., visibility, moderation)
- One Python snapshot generation step handles both
- Reduce cycle overhead (planning/testing unified)

**Cons**:
- Larger scope increases risk
- More moving parts (two route handlers, two snapshot types)
- More complex parity testing

**Effort**: High (25-35 hours, more coordination required)

---

### Option C: Generalized Snapshot Framework First
**Approach**: Refactor the board index snapshot pattern into a reusable framework (route-agnostic snapshot builder, PHP-side loader/router), then layer threads, profiles, posts quickly.

**Pros**:
- Eliminates per-route boilerplate after initial framework
- Easier to add 4th, 5th routes later
- Cleaner codebase (DRY principle)
- Single snapshot refresh hook covers all routes

**Cons**:
- Upfront effort on abstraction (risk of over-engineering)
- Framework complexity may be premature (haven't validated 2nd route yet)
- Testing framework complexity adds overhead

**Effort**: Very High (35-50 hours, includes refactor + threads + profiles)

---

### Option D: Posts Only Next (Lowest Risk)
**Approach**: Implement posts (`/posts/{id}`) before threads because:
- Posts are typically simpler (single entity + parent context)
- Smaller HTML surface (no discussion tree)
- Validates the pattern scales to a third independent route type
- Threads can follow with lessons learned

**Pros**:
- Validation step before threads (higher complexity)
- Fastest safe next step
- De-risks thread expansion assumptions

**Cons**:
- Posts are lower traffic (less business value)
- Delays thread caching (highest-value route)
- Takes longer to see meaningful performance impact

**Effort**: Medium (12-18 hours)

---

## Recommendation: **Option A (Threads First)**

Start with `/threads/{id}` expansion as the second PHP-native route because:

1. **Traffic impact**: Thread pages are the 2nd most-accessed route after board index
2. **Pattern validation**: Reuses proven 4-stage methodology (low risk relative to A/B/C)
3. **Clear scope boundary**: Threads are self-contained (one route, one snapshot type)
4. **Incremental learning**: Lessons from thread expansion guide profile/post decisions

### Execution Plan

**Phase 1: Thread Route Expansion (this cycle)**
- Stage 1: Define thread read contract (visibility, query boundaries, cache invalidation)
- Stage 2: Build SQLite-backed thread snapshot infrastructure in Python
- Stage 3: Implement PHP thread renderer
- Stage 4: Parity testing + operator checklist

**Phase 2: Profile Route (next cycle, conditional)**
- Depends on Phase 1 success
- Likely simpler than threads (less nesting, data-rich)

**Phase 3: Post Route (future cycle)**
- Lowest priority (lowest traffic)
- Best deferred until threads + profiles prove the expansion pattern

### Expected Outcomes

- **Performance**: Cache hits on `/threads/*` move from 50–100ms (Python) to ~10–30ms (PHP native)
- **Throughput**: Peak traffic capacity +40–60% due to fewer concurrent Python processes
- **Operator value**: Clear template for expanding to additional routes as needed

---

## Open Questions

1. **Thread snapshot storage**: Use a dedicated SQLite database (`state/cache/php_native_reads.sqlite3`) for thread snapshots. Do not introduce per-thread JSON files in this phase.
2. **Fallback precedence**: Prefer static HTML when present. Native PHP thread rendering should be attempted only after the static HTML lookup misses.
3. **Read-time repairs**: Read fallback should not rebuild or repair SQLite snapshots inline. Snapshot refresh remains an eager write-time responsibility; operators can use separate rebuild tooling if needed.
4. **Query parameters on threads**: `?format=rss` or `?view=expanded` stay Python-only; only bare `/threads/{id}` is eligible for native rendering.
5. **Profile complexity**: Profiles should remain deferred until after thread expansion proves successful.
