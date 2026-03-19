## Problem Statement
Choose the simplest way to make the one-time username-claim opportunity more visible to eligible users without reintroducing dead-end UI for ineligible profiles.

### Option A: Add an eligibility-aware username-claim callout in the profile page header/hero
- Pros:
  - Makes the opportunity visible immediately, where new users are already looking.
  - Fits the request directly because the page header is a strong, obvious location.
  - Can remain hidden for ineligible profiles, so the new prominence does not reintroduce dead-end affordances.
- Cons:
  - Requires touching the shared profile-page header messaging, not just the action cluster.
  - Risks crowding the hero if the copy is too heavy.

### Option B: Keep the header generic and strengthen the in-page action cluster only
- Pros:
  - Smaller surface change because it stays inside existing profile actions.
  - Avoids adding more messaging to the hero area.
  - Keeps the invitation close to the actual button.
- Cons:
  - Easier for new users to miss because the action cluster is visually secondary to the page header.
  - Less effective at teaching the one-time claim opportunity.

### Option C: Add a dedicated onboarding/status panel elsewhere on the profile page
- Pros:
  - Creates room for more explanation than the header or action cluster can comfortably hold.
  - Could later grow into broader account-status guidance.
- Cons:
  - Larger scope than the immediate need.
  - Adds another profile-page section for a narrow affordance problem.
  - Risks turning a simple visibility fix into a broader onboarding/UI loop.

## Recommendation
Recommend Option A: add an eligibility-aware username-claim callout in the profile page header/hero.

This is the clearest answer to the user need. Eligible new users should see the one-time username-claim opportunity prominently as soon as the profile loads, while ineligible users should still see nothing. That keeps the affordance discoverable without undoing the recent work to hide dead-end update actions.
