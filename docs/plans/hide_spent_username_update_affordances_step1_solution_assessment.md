## Problem Statement
Choose the simplest way to stop showing username-update actions once a signer identity has already used its one allowed username claim.

### Option A: Hide the `update username` affordance everywhere once the viewed signer identity already has a visible claim
- Pros:
  - Best matches the new product rule because users no longer see an action they cannot successfully use.
  - Reduces dead-end navigation and avoids predictable forbidden errors.
  - Keeps the public profile and merge-management pages cleaner after the one-time claim is spent.
- Cons:
  - Users lose a direct path to the explanatory update page after claiming a name.
  - Requires the read layer to expose whether the viewed signer identity has already spent its claim.

### Option B: Keep the affordance visible, but disable or relabel it once the claim is spent
- Pros:
  - Preserves a visible explanation point for the one-claim policy.
  - Makes the state change explicit without hiding functionality entirely.
  - May reduce confusion for users who remember seeing the action earlier.
- Cons:
  - Still leaves non-actionable UI on pages that should stay focused.
  - Requires more copy and state handling on public pages.
  - Can feel like clutter if the only outcome is “you already used this.”

### Option C: Keep the current links and rely on the update page/backend rejection to explain the policy
- Pros:
  - Smallest immediate change.
  - Reuses the existing page copy and deterministic rejection behavior.
- Cons:
  - Leaves a known dead-end in the main profile UI.
  - Makes users click through to learn something the UI already knows.
  - Weakest fit with the one-time-claim product rule.

## Recommendation
Recommend Option A: hide the `update username` affordance everywhere once the viewed signer identity already has a visible claim.

This is the cleanest user experience for the new system. The product rule is now “one claim per key pair,” so the main read surfaces should stop advertising a write action after that claim is spent. If later we want a dedicated explanatory history surface, that can be added separately without keeping a dead-end primary action in place.
