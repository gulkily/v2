## Problem Statement
Choose the smallest useful way to let a browser user update their username/display name through the existing web app now that signed `update_profile` submissions already exist, without turning the next loop into full account settings, session auth, or a generic write-surface rewrite.

### Option A: Add a dedicated profile-update page inside the existing web app
- Pros:
  - Smallest path to a real frontend username-edit flow because it can reuse the current browser key storage/signing pattern and the existing `update_profile` API contract.
  - Keeps the public profile page read-only and avoids needing owner detection before showing edit controls.
  - Fits the current product shape where write actions live on explicit compose-style pages rather than inside read views.
  - Gives users a focused flow for entering one new username and seeing the signed preview or result immediately.
- Cons:
  - Adds another standalone write screen and route.
  - May duplicate some compose-page template or browser-signing behavior unless the shared pieces are lightly extracted.
  - Requires the user to navigate to a separate page before seeing the updated profile read back.

### Option B: Add inline username editing directly on the profile page
- Pros:
  - Most obvious user experience because the edit action sits beside the current displayed name.
  - Makes read-after-write feedback immediate on the same page.
  - Could reduce navigation if a user is already looking at their profile.
- Cons:
  - The app has no session/auth model, so deciding when to show or enable edit controls becomes awkward and potentially confusing.
  - Pushes the loop toward local-key ownership detection on a public read surface.
  - Mixes signer-specific write behavior into a page that currently works for every viewer and identity alias.
  - Makes the first frontend slice harder to keep narrow because profile-page behavior, permissions messaging, and failure states grow together.

### Option C: Generalize the browser compose UI into one reusable signed-action shell before adding username updates
- Pros:
  - Creates a consistent browser pattern for posts, profile updates, identity links, and later signed actions.
  - Reduces long-term duplication across templates and client-side signing logic.
  - Keeps all write flows aligned with one shared UX and technical contract.
- Cons:
  - Larger scope than the user story requires right now.
  - Reopens architecture questions about a general action framework before the specific username-update flow is proven useful.
  - Delays the first simple frontend solution for a capability the backend already supports.

## Recommendation
Recommend Option A: add a dedicated profile-update page inside the existing web app.

This is the smallest coherent slice because the main gap is no longer the record model or API contract; it is only the browser-facing submission path. The loop should stay strict about boundaries:

- Reuse the current local browser key model and signed `update_profile` contract.
- Focus on one field: setting or replacing the current username/display name.
- Keep the public profile page read-oriented, with at most simple links into the dedicated update flow.
- Avoid session/auth work, generic multi-action browser refactors, avatars, bios, and broader account settings.

That gives the product a real frontend answer to the user story quickly: a browser user can open an explicit page, sign a username change with their local key, submit it, and then read the updated name through the existing profile and attribution surfaces. The tradeoff is one more focused write page, but that is cleaner than overloading the profile view or starting a larger frontend framework loop.
