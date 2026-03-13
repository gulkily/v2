## Problem Statement
Choose how broad the first implementation slice should be for repository layout and canonical post format without turning the first loop into a full-system design exercise.

### Option A: Minimal canonical post slice
- Pros:
  - Smallest scope and fastest path to a demonstrable result.
  - Produces immediately inspectable sample data in git.
  - Defers identity, moderation, indexes, and sync details until later loops.
- Cons:
  - Some future directory and record decisions remain open.
  - Later loops may need light structural expansion.

### Option B: Full repository skeleton slice
- Pros:
  - Establishes posts, moderation, identity, tombstones, and index directories up front.
  - Reduces later ambiguity about where new record types belong.
  - Makes the long-term architecture feel more settled early.
- Cons:
  - Pulls too much future scope into the first loop.
  - Risks speculative structure before read/write behavior is proven.
  - Slows down the first visible demo.

### Option C: Repository plus derived-index slice
- Pros:
  - Gives early confidence that board-tag and thread lookup patterns fit the data model.
  - Moves the project closer to the later read-only web and API loops.
  - Surfaces determinism issues earlier.
- Cons:
  - Couples Loop 1 to query and rendering concerns.
  - Makes the first loop substantially larger than just canonical storage.
  - Encourages accidental drift into Step 2 and 3 work for later slices.

## Recommendation
Recommend Option A: minimal canonical post slice.

It best fits the goal of shrinking the architecture into FDP-sized loops with an early demo. The first loop should prove that one-file-per-post ASCII records and a stable on-disk layout feel right in git before the project commits to indexes, moderation records, or broader repository machinery.
