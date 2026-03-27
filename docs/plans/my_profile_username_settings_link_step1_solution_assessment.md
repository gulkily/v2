## Problem Statement
Choose the simplest way to add a username-settings link on the self-profile page (`?self=1`) only when that username-update option is available to the current profile.

### Option A: Add an eligibility-aware username action directly in the self-profile action row
- Pros:
  - Matches the request directly because the link lives on the `My profile` page itself.
  - Reuses the existing profile action area instead of introducing a new panel or page section.
  - Can stay hidden when the profile is not eligible, so it does not reintroduce dead-end UI.
- Cons:
  - Requires the profile render path to distinguish self-profile requests from normal public profile views.
  - Shares limited space with existing actions like merge management.

### Option B: Add a dedicated self-profile callout/panel for username setup
- Pros:
  - Gives the link more visual prominence than a small action chip.
  - Leaves room for explanatory copy about when username setup is available.
  - Scales better if the self-profile page later gains more account-management guidance.
- Cons:
  - Larger UI change than the request needs.
  - Adds another section to a page that is currently mostly public-profile content.
  - Risks overlapping with the existing username-claim CTA patterns elsewhere in the app.

### Option C: Keep the self-profile page unchanged and rely on the existing global username-claim CTA surfaces
- Pros:
  - Smallest implementation change.
  - Avoids touching the profile page render path.
  - Preserves one central place for the username setup invitation.
- Cons:
  - Does not satisfy the request for a link on `My profile`.
  - Makes the setting harder to discover when users intentionally navigate to their profile for account actions.
  - Keeps the account-management path split across separate surfaces.

## Recommendation
Recommend Option A: add an eligibility-aware username action directly in the self-profile action row.

This is the narrowest change that satisfies the request without adding new page structure. The `My profile` route already serves as the user’s account-facing profile surface, so a conditional action there is the cleanest place to expose username setup when the profile can still use it.
