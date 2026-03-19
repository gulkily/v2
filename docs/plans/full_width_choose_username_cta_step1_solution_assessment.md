## Problem Statement
Choose the simplest way to make the initial username-claim action visible near the top of every page for a user who has a stored browser key but has not yet chosen a username.

### Option A: Add a shared site-wide top-of-page `Choose a username` CTA for eligible browser-key sessions
- Pros:
  - Best matches the requested behavior because the CTA appears on every page, not just profile views.
  - Makes the next step obvious immediately after a user starts browsing with a stored key and no username.
  - Keeps the existing `/profiles/<identity>/update` flow as the destination instead of inventing a second username-claim path.
- Cons:
  - Broadens the feature from repository-state profile rendering into shared page chrome plus browser-key/session awareness.
  - Requires a clear rule for which identity/update URL to target when the browser has a stored key.

### Option B: Keep the CTA profile-only, but make it full-width and near the top
- Pros:
  - Smaller change because it stays inside existing profile-page rendering.
  - Reuses the current server-side eligibility rule without depending on browser-local state.
- Cons:
  - Does not satisfy the new requirement that the CTA be visible on every page.
  - Still depends on users reaching a profile page before discovering the username-claim action.

### Option C: Add a shared header/nav indicator instead of a dedicated top-of-page section
- Pros:
  - Reaches every page through the shared layout.
  - Smaller visual footprint than a full-width section.
- Cons:
  - Weaker emphasis than the requested dedicated near-top CTA.
  - More likely to be overlooked, especially by first-time users who do not yet understand the account model.

## Recommendation
Recommend Option A: add a shared site-wide top-of-page `Choose a username` CTA for eligible browser-key sessions.

This matches the clarified product goal. The CTA should no longer be modeled as a profile-page enhancement. It should become a shared page-level affordance shown only when the browser has a stored key and the corresponding signer identity has not yet used its one username claim. The existing update page and backend policy can remain unchanged.
