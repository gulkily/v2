# Post Index Rebuild Frequency Reduction Step 1: Solution Assessment

## Problem Statement
Choose the smallest coherent way to stop ordinary reads from triggering full post-index rebuilds more often than the underlying repo state actually requires.

### Option A: Add a schema-compatibility hash so full rebuilds are required only when the indexed schema shape is actually incompatible
- Pros:
  - Separates true rebuild-required schema changes from ordinary newer-commit cases.
  - Gives operators a more precise reason why a full rebuild is required.
  - Preserves the current request-time freshness model while making schema checks less blunt.
  - Creates a stable compatibility signal that later features can reuse.
- Cons:
  - Only addresses rebuilds caused by schema incompatibility checks, not ordinary head drift by itself.
  - Requires careful definition of what counts as schema-compatible versus rebuild-required.

### Option B: When the schema is compatible, fast-forward the index from the indexed head through later commits instead of rebuilding from scratch
- Pros:
  - Directly targets the common case where repo history has advanced but the existing index is still structurally usable.
  - Reduces unnecessary full rebuilds without changing the canonical read surfaces.
  - Matches operator intuition better than treating every head mismatch as a full rebuild.
  - Can preserve full rebuilds as the fallback when incremental catch-up is not safe.
- Cons:
  - Broader than a pure readiness-check tweak because it changes stale-index recovery behavior.
  - Requires confidence that commit-by-commit catch-up can recover all relevant post, identity, and profile-derived index state.
  - May expose edge cases around history rewrites, non-post paths, or missing commit metadata.

### Option C: Tighten the current stale-readiness checks using existing metadata only
- Pros:
  - Smallest immediate surface area.
  - Keeps the feature focused on correctness of rebuild triggers rather than rebuild speed.
  - Preserves the current request-time rebuild architecture and operator expectations.
- Cons:
  - May not be enough if the main problem is that head mismatch currently falls straight to full rebuild.
  - Leaves schema compatibility implicit rather than making it a first-class decision point.
  - Risks producing only a marginal improvement if false positives come from the recovery strategy rather than the check itself.

## Recommendation
Recommend Option B: when the schema is compatible, fast-forward the index from the indexed head through later commits instead of rebuilding from scratch.

This is the smallest option that directly addresses the likely source of unnecessary full rebuilds: treating ordinary newer-commit drift as rebuild-required even when the current index shape is still usable. Step 2 should likely pair this with an explicit schema-compatibility signal, so the decision becomes: full rebuild only when schema compatibility is broken, otherwise incremental catch-up from the indexed head to the current head.
