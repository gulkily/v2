## Problem Statement
Choose the smallest coherent way to show more commit detail in `/activity/` and add a GitHub commit link without turning the page into a full git browser.

### Option A: Enrich the existing activity commit cards with more metadata and a GitHub link
- Pros:
  - Best fit for the request because it keeps `/activity/` as the main repository-history surface and adds the missing commit detail directly where users already look.
  - Reuses the current commit-card model instead of introducing another route or interaction layer.
  - Keeps scope narrow: more commit context, clearer touched-file information, and a GitHub link can all be expressed inside the current timeline and filters.
  - Fits the “link is OK even if it does not exist yet” requirement because link generation can be deterministic from repo settings and commit id.
- Cons:
  - Requires deciding which additional commit facts are useful without making each card too dense.
  - Needs one source of truth for building the GitHub commit URL.

### Option B: Keep `/activity/` compact and add a separate commit-detail page per commit
- Pros:
  - Lets the activity timeline stay visually light while still allowing richer commit information.
  - Creates a cleaner place for future commit-specific enhancements if those grow later.
- Cons:
  - Does not satisfy the request as directly because users still have to click through to understand what happened in a commit.
  - Adds a new route and navigation contract for a feature that may only need modest extra metadata.
  - Makes the GitHub link less useful on the main timeline because the timeline remains under-informative.

### Option C: Expand `/activity/` toward a lightweight git browser with file lists, diffs, and outbound links
- Pros:
  - Could provide the richest explanation of repository changes in one place.
  - Leaves room for future engineering-oriented history inspection without more page-model changes.
- Cons:
  - Larger scope than the request.
  - Pulls the activity page toward a generic code-hosting UI instead of a concise repository-history view.
  - Increases rendering and testing complexity before the smaller commit-detail enhancement is proven sufficient.

## Recommendation
Recommend Option A: enrich the existing activity commit cards with more metadata and a GitHub link.

This is the smallest approach that fulfills “show more information about what happened in a commit” while preserving the current filtered timeline model. The next steps should stay disciplined: add a small set of high-signal commit details, generate a deterministic GitHub commit URL, and avoid drifting into a dedicated git-browser experience.
