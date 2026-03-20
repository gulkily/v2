## Problem Statement
Choose the safest and simplest way to show browser-stored private key material only on the current user's own profile page, without implying that other profiles share that local key.

### Option A: Keep the private-key block visible on every profile page
- Pros:
  - Smallest immediate change because the current profile template already renders the block everywhere.
  - Makes the key viewer easy to find regardless of which profile page the user is visiting.
- Cons:
  - Misleading because it suggests the viewed profile is tied to the local browser key when it may not be.
  - Creates unnecessary exposure of private-key UI on other users' pages.
  - Weakens the mental model that private key material is local, personal, and identity-specific.

### Option B: Show the private-key block only when the viewed profile matches the browser-stored key identity
- Pros:
  - Best matches user expectations: private key material appears only on "my" profile.
  - Preserves the existing profile page shape while avoiding a separate key-management surface.
  - Can be enforced client-side using the already stored public key and derived identity match.
- Cons:
  - Requires a small amount of profile-page identity-aware client logic instead of a static block.
  - The page may look slightly different depending on whether the browser has a matching key saved.

### Option C: Remove the private-key block from profile pages and expose it only on a dedicated account/key page
- Pros:
  - Clearest separation between public profile viewing and private local key management.
  - Avoids any ambiguity about whether the key viewer belongs to the viewed profile.
- Cons:
  - Larger UX change because users must learn a new destination for their key material.
  - Adds another page or route for a relatively narrow need.
  - Moves away from the current "profile as account hub" direction.

## Recommendation
Recommend Option C: remove the private-key block from profile pages and expose it only on a dedicated account/key page.

This creates the clearest boundary between public profile viewing and private local key management. It also avoids implying that any viewed profile is tied to the browser-stored private key.
