# Post Index Rebuild Duration Reduction Step 1: Solution Assessment

## Problem Statement
Choose the smallest coherent way to reduce the time a legitimate full post-index rebuild takes once it has been triggered.

### Option A: Optimize the expensive rebuild sub-step inside the existing full rebuild flow
- Pros:
  - Directly targets operator-visible rebuild duration without changing when rebuilds happen.
  - Preserves the current rebuild contract, request flow, and index shape.
  - Keeps the feature narrow and measurable around one maintenance path.
  - Fits the current evidence that a specific rebuild phase is disproportionately expensive.
- Cons:
  - Improvement may be capped if other rebuild phases become dominant later.
  - Requires careful measurement so optimization work stays focused on the real bottleneck.

### Option B: Introduce broader incremental or cached derivation so full rebuilds reuse more prior work
- Pros:
  - Could produce larger speedups across repeated rebuilds.
  - May create reusable seams for other write or maintenance paths later.
- Cons:
  - Broader scope because it changes more of the rebuild model and derived-data lifecycle.
  - Increases correctness risk if cached derived data becomes invalid or incomplete.
  - Can turn a focused performance slice into a partial indexing redesign.

### Option C: Shift legitimate rebuilds off the user-critical path instead of making the rebuild itself faster
- Pros:
  - Reduces user-facing wait even if absolute rebuild cost stays high.
  - Leaves room for richer background execution later.
- Cons:
  - Does not actually reduce rebuild duration for operators or maintenance runs.
  - Broadens the scope into job orchestration and stale-data behavior.
  - Solves a different problem than rebuild speed itself.

## Recommendation
Recommend Option A: optimize the expensive sub-step within the existing full rebuild flow.

This is the smallest coherent slice because the goal is to make legitimate rebuilds finish faster, not to redesign rebuild triggering or move work into a background system. The next step should stay focused on measuring and reducing the dominant rebuild cost while preserving the current canonical indexing lifecycle.
