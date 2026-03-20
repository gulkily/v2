## Problem Statement
Choose the smallest coherent way to make `/activity/?view=...` faster while also ensuring slow activity loads appear in the in-app recent slow operations surface.

### Option A: Treat this as one focused `/activity/` performance-and-observability slice
- Pros:
  - Fits the actual operator problem: a slow route that is also hard to diagnose because its timings are not meaningfully visible in the existing operations UI.
  - Keeps scope narrow by reusing the current `/activity/` route and the existing operation-event store instead of inventing new monitoring surfaces.
  - Allows the first fix to improve both user experience and diagnosis at the same time by adding route-specific timing visibility before or alongside targeted performance reductions.
  - Creates a clean path to make the “recent slow operations” panel reflect recent slow `/activity/` loads rather than leaving activity performance opaque.
- Cons:
  - Slightly broader than a pure latency fix because it also touches the visibility/reporting path.
  - Requires care to keep the work limited to `/activity/` and the current operation-events surface rather than expanding into general observability work.

### Option B: Optimize `/activity/` only and defer slow-operation visibility
- Pros:
  - Smallest user-facing performance scope.
  - Keeps attention on the route that feels slow right now.
- Cons:
  - Leaves diagnosis weak if the first optimization is incomplete or a regression returns later.
  - Does not solve the reported mismatch between slow page loads and the recent-slow-operations surface.
  - Risks repeated guesswork because the route remains under-instrumented.

### Option C: Rework the operator performance panel first and defer `/activity/` optimization
- Pros:
  - Could improve observability across more routes than `/activity/`.
  - May clarify whether the slowest cost is request timing, git work, repository loading, or reporting/query behavior.
- Cons:
  - Does not directly improve the slow page the user is feeling.
  - Risks turning a route-level issue into a broader operator-dashboard project.
  - Delays the user-visible latency improvement.

## Recommendation
Recommend Option A: treat this as one focused `/activity/` performance-and-observability slice.

This is the smallest option that addresses both halves of the problem without drifting into a larger monitoring project. The next step should stay tight: make `/activity/` timing visible through the existing operation-events path, then use that visibility to reduce the route’s avoidable work and ensure the recent-slow-operations surface reflects recent slow activity requests correctly.
