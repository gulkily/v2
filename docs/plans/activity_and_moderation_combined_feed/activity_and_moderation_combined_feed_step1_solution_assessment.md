## Problem Statement
Choose the smallest coherent way to combine the current site activity page and moderation log into one filtered page without turning the next loop into a broader event-system redesign.

### Option A: Merge `/activity/` and moderation records into one canonical activity page with fixed filters
- Pros:
  - Best fit for the request because it creates one page that can show both git-backed site activity and moderation events with explicit filtering.
  - Reuses the existing `/activity/` route as the broader “what happened on this instance” surface.
  - Keeps scope focused on one merged read view plus simple fixed filters such as all activity, content activity, and moderation activity.
  - Avoids making users choose between two nearby logs when they really want one timeline with filtering.
- Cons:
  - Requires deciding how to interleave two currently separate data shapes on one page.
  - The existing moderation-only page and activity-only page contracts will need consolidation.

### Option B: Keep `/activity/` as the main page but add links between it and a separate filtered moderation page
- Pros:
  - Smallest UI disruption because the current routes can stay specialized.
  - Easier to implement if the feed item shapes stay separate.
- Cons:
  - Does not satisfy the request as directly because users still have to move between two pages.
  - Keeps duplicated navigation and mental overhead around “activity” versus “moderation log.”
  - Makes filter behavior weaker because the most important filter boundary is still expressed as a route split.

### Option C: Replace both pages with a broader normalized event feed model
- Pros:
  - Could produce the cleanest long-term architecture if posts, replies, commits, and moderation actions all become one unified event stream.
  - Gives future features one obvious home for filters, ordering, and event metadata.
- Cons:
  - Larger scope than the current request.
  - Pulls the next steps toward a new generalized event model instead of a focused page merge.
  - Increases risk of churn across current activity and moderation rendering before the merged-page behavior is proven useful.

## Recommendation
Recommend Option A: merge `/activity/` and moderation records into one canonical activity page with fixed filters.

This is the smallest approach that actually fulfills “combine site activity and moderation log into one page with filters.” The next steps should keep it narrow: one canonical route, one merged page, one shared ordering model, and a few explicit filter modes rather than a broader event-system rewrite.
