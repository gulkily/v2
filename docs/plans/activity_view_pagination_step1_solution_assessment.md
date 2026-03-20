## Problem Statement
Choose the smallest coherent way to let users browse all activity in each `/activity/` filter view with pagination, while preserving the current single-page activity route and avoiding misleading gaps caused by the existing “fetch 12 then filter” approach.

### Option A: Keep the current `/activity/` route and add query-string pagination per filter view
- Pros:
  - Best fit for the existing product shape because the current UI already uses one route with `view=all|content|moderation|code`.
  - Smallest user-facing change: users keep the same tabs and gain `Older` / `Newer` navigation or page links.
  - Lets each filter fetch enough matching events for that specific view instead of filtering only the latest 12 global commits.
  - Reuses the current activity event model, filter nav, and renderer without inventing a second activity surface.
- Cons:
  - Requires a real paging contract for two different backing sources: git commits for content/code and moderation records for moderation.
  - The `all` view is trickier because it merges multiple event streams and needs a stable combined ordering across pages.
  - Cursor or page parameters need careful design so switching between views does not create confusing empty pages.

### Option B: Keep `/activity/` for the first page only and add dedicated paginated subroutes per activity type
- Pros:
  - Simpler backend logic for each individual feed because content, moderation, and code can paginate independently with their own rules.
  - Makes it easier to optimize each view later without one generic pagination layer carrying all cases.
  - Reduces the complexity of the `all` timeline if that view is left as a recent overview only.
- Cons:
  - Splits the activity experience into multiple destinations when the current product already presents activity as one navigable page.
  - Introduces more routing and navigation complexity than the user asked for.
  - Makes `all` feel second-class or inconsistent unless it also receives a full pagination design.

### Option C: Add a “Load more” button that progressively appends older results on the same page
- Pros:
  - Friendly interaction model for users who just want to keep scrolling.
  - Can avoid visible page numbers and preserve the current lightweight activity layout.
  - Potentially reusable for other stream-like pages later.
- Cons:
  - Still needs the same underlying paging logic on the backend, so it does not really reduce implementation complexity.
  - Harder to keep linkable/shareable state for specific positions in the timeline unless query parameters are still introduced.
  - More front-end state and progressive enhancement work than a straightforward paginated GET flow.

## Recommendation
Recommend Option A: keep the current `/activity/` route and add query-string pagination per filter view.

This is the smallest coherent extension of the current design. The page already has stable filter parameters, so pagination should build on that rather than introducing new routes or a JS-only loading model. The key technical correction is that each view must page over its own matching activity set, not over the latest 12 repository commits and then filter afterward.

That likely means:

- `view=content` fetches enough content-classified commits to fill one page
- `view=code` fetches enough code-classified commits to fill one page
- `view=moderation` pages through moderation records directly
- `view=all` uses a stable merged ordering across event kinds, then paginates that merged list

The implementation difficulty is moderate, with the hardest part being the `all` view because it merges different event sources. But that is still a better tradeoff than fragmenting the route structure or introducing client-side “load more” behavior first. A plain paginated GET design keeps the feature linkable, testable, and consistent with the rest of the site.
