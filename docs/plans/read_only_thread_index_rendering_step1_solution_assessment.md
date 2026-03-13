## Problem Statement
Choose the smallest useful way to implement read-only thread and index rendering without dragging the next loop into API design, write paths, or premature indexing machinery.

### Option A: Direct-read web renderer
- Pros:
  - Fastest path to a visible demo for humans.
  - Reuses the current canonical files as the only source of truth.
  - Keeps the loop focused on board index, thread view, and permalink rendering.
- Cons:
  - May need light refactoring later if shared read logic is extracted for the API loop.
  - Large datasets may eventually need stronger indexing support.

### Option B: Derived-index-first renderer
- Pros:
  - Surfaces deterministic grouping and ordering questions early.
  - Could make later reads faster and more uniform.
  - Starts building machinery useful for larger repositories.
- Cons:
  - Pulls future index policy into the rendering loop.
  - Adds complexity before the simplest reader is proven valuable.
  - Risks making Loop 2 too large.

### Option C: Shared web-and-API read layer in one loop
- Pros:
  - Avoids duplicated parsing work across Loop 2 and Loop 3.
  - Produces a stronger baseline for future backends.
  - May reduce later reshaping of reader code.
- Cons:
  - Bundles two checklist items into one loop.
  - Slows down the first visible web demo.
  - Expands scope beyond what the checklist intends for Loop 2.

## Recommendation
Recommend Option A: direct-read web renderer.

It is the smallest slice that makes the project visibly real for humans while preserving the current loop boundaries. The next loop should prove that canonical text files can be parsed and rendered into board indexes, thread pages, and permalinks before the project adds derived indexes or API surfaces.
