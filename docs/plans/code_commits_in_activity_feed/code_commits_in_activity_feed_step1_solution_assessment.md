## Problem Statement
Choose the smallest coherent way to include non-content repository commits such as code changes in the merged activity timeline and add a filter for them without turning `/activity/` into a full generic git browser.

### Option A: Extend the merged activity page with a new code-commit event type and fixed filter
- Pros:
  - Best fit for the request because it keeps the existing merged `/activity/` page and adds one more explicit event class plus filter.
  - Reuses the current git-commit activity machinery instead of introducing a separate code-history route.
  - Keeps scope narrow: all activity, content activity, moderation activity, and code activity can still live in one filtered timeline.
  - Preserves the current mental model that `/activity/` is the canonical “what happened here” page.
- Cons:
  - Requires deciding how code commits should be represented when they do not touch canonical post files.
  - Needs one clear rule for separating content commits from code commits when a commit touches both kinds of files.

### Option B: Keep `/activity/` focused on content and moderation, and add a separate code-history page
- Pros:
  - Simplest way to avoid mixing product/content activity with engineering changes.
  - Lets the code-history page specialize in repository details without affecting the current activity timeline.
- Cons:
  - Does not satisfy the request as directly because the new commits would not appear in the existing activity log.
  - Splits instance history across more pages again right after the merged-feed consolidation.
  - Makes filtering weaker because the most important new filter boundary becomes a route split instead of an in-page filter.

### Option C: Expand `/activity/` into a broader all-commits repository event browser
- Pros:
  - Could produce the most complete view of repository history.
  - Avoids future piecemeal additions if more commit classes are needed later.
- Cons:
  - Larger scope than the current request.
  - Pulls the next steps toward a generic git browsing tool instead of a focused extension of the current filtered activity page.
  - Risks burying moderation and user-visible content events inside a noisier engineering timeline before the lighter code-commit extension is proven useful.

## Recommendation
Recommend Option C: expand `/activity/` into a broader all-commits repository event browser.

This matches the chosen direction: `/activity/` should become the broader repository-history surface rather than only a content-plus-moderation timeline. The next steps should still stay disciplined inside that larger direction: define clear commit classes such as content, moderation, and code, keep fixed filters instead of arbitrary query tooling, and avoid drifting all the way into a general-purpose git UI.
