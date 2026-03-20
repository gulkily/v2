## Problem Statement
Choose the smallest coherent way to give users clear feedback when a request triggers post-index reindexing, instead of leaving them with an unexplained long page load.

### Option A: Keep request-triggered reindexing but show an explicit in-app loading state tied to the reindex operation
- Pros:
  - Directly solves the user-facing problem without requiring a larger architecture change.
  - Fits the current system shape, where ordinary requests can still trigger a rebuild when the index is stale.
  - Creates a path to reuse existing slow-operation or timing visibility rather than inventing a second status model.
  - Keeps the slice focused on clarity and responsiveness instead of turning it into a background-jobs project.
- Cons:
  - Users still wait for the rebuild to finish before seeing the requested page content.
  - Requires careful UX so the feedback feels informative rather than like a generic spinner.

### Option B: Move reindexing into a background task and return a pending or stale-data state immediately
- Pros:
  - Gives the fastest initial response because the request no longer blocks on the full rebuild.
  - Can eventually support richer progress reporting, retries, and task status.
- Cons:
  - Significantly broader scope because it introduces background-job lifecycle, task ownership, and stale-data behavior.
  - Forces product decisions about what the user sees while data is incomplete or outdated.
  - Risks expanding this slice far beyond the immediate feedback problem.

### Option C: Leave the request flow unchanged and improve only passive affordances like copy, skeletons, or generic busy indicators
- Pros:
  - Smallest visual-only change.
  - Low implementation risk.
- Cons:
  - Does not tell the user why the page is slow or that reindexing is the cause.
  - Leaves operators and users with weak diagnosis when rebuilds happen unexpectedly.
  - Risks feeling like cosmetic loading polish rather than meaningful feedback.

## Recommendation
Recommend Option A: keep request-triggered reindexing for now, but show an explicit in-app loading state tied to the rebuild.

This is the smallest option that addresses the real UX problem without widening the feature into background processing or partial-data design. The next step should stay tight: make reindex-triggered waits visible and understandable to the user, ideally by reusing the existing operation-visibility model so the same work is explainable in both user-facing and operator-facing surfaces.
