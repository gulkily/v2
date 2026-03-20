## Problem Statement
Choose the safest and simplest way to mothball the unfinished account merge feature behind a default-off flag without creating inconsistent UI or breaking existing read paths.

### Option A: Hide only the merge UI entry points while leaving merge APIs and assets active
- Pros:
  - Smallest immediate surface-area change.
  - Lets developers still reach the feature directly for manual testing.
- Cons:
  - Incomplete because direct routes, nav notifications, and API calls still expose the feature.
  - Increases confusion by making the feature feel half-disabled instead of clearly unavailable.
  - Risks accidental use in production through deep links or existing automation.

### Option B: Gate all merge-specific web surfaces and merge-related navigation behind one shared feature flag
- Pros:
  - Clear product posture: the feature is off unless explicitly enabled.
  - Keeps the implementation narrow by reusing one shared flag across profile links, merge suggestion UI, merge pages, merge nav behavior, and merge assets.
  - Preserves existing merge records and core identity resolution logic without deleting unfinished work.
- Cons:
  - Requires careful auditing so every merge-related UI/API surface uses the same flag consistently.
  - Developers must enable the flag locally when continuing work on the feature.

### Option C: Revert the merge feature entirely from the product
- Pros:
  - Eliminates all current user-facing confusion.
  - Avoids carrying disabled code paths in production.
- Cons:
  - Much larger change because merge-aware identity behavior, pages, APIs, tests, and related records are already integrated.
  - Throws away unfinished but valuable work instead of mothballing it.
  - Makes later resumption slower and riskier than keeping the feature dormant behind a flag.

## Recommendation
Recommend Option B: gate all merge-specific web surfaces and merge-related navigation behind one shared feature flag that is off by default.

This best matches the stated goal of mothballing rather than removing the feature. It makes the release posture explicit, avoids half-enabled UI leaks, and keeps the existing implementation available for future development when the flag is turned back on.
