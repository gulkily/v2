## Problem
Users who have a stored browser key but have not yet claimed a username should see that next step clearly near the top of every page. The CTA should feel like a primary action, not a profile-only affordance, while still avoiding dead-end UI for users who are no longer eligible.

## User Stories
- As a first-time user who has generated or imported a browser key but has not chosen a username yet, I want to see an obvious near-top CTA on every page so I understand the next account step immediately.
- As a returning user who already has a stored key but still has no username, I want the same CTA to keep reminding me across pages so I can complete the missing setup step when convenient.
- As a user who has already claimed a username, I do not want to keep seeing the CTA once it no longer applies.
- As a reader of the codebase, I want the visibility and target rules for this CTA to be explicit so every page renders consistent guidance for the same stored-key state.

## Core Requirements
- The app must show one prominent near-top `Choose your username` CTA on shared pages when the browser has a stored key whose signer identity is still eligible to make its one username claim.
- The CTA must remain hidden when there is no stored browser key, when the stored key cannot be resolved to a profile/update target, or when that signer identity has already spent its username claim.
- The CTA must appear through shared page layout/chrome so it is visible on every normal page, not only on profile pages.
- The CTA must lead into the existing `/profiles/<identity-slug>/update` flow for the eligible signer identity rather than introducing a second username-claim path.
- The CTA copy may include short supporting text, but it must stay action-oriented and avoid device-specific wording such as `click` or `tap`.
- The slice must not change the existing backend one-claim policy or the existing update submission contract.

## Shared Component Inventory
- Existing shared page shell in `forum_web/templates.py`: extend this so a site-wide near-top CTA can render consistently across normal pages.
- Existing browser-stored key handling in the frontend assets: reuse this to determine whether a local key is present and which identity it maps to.
- Existing profile/update targeting logic: reuse the current canonical `/profiles/<identity-slug>/update` destination for the resolved eligible signer identity.
- Existing username-claim eligibility rule: reuse the current one-claim-per-signer policy rather than inventing a second interpretation of eligibility.
- Existing profile-page CTA work: treat it as superseded by the shared page-level CTA for this slice instead of maintaining two competing primary prompts.

## Simple User Flow
1. A user visits any normal page in the app with a stored browser key.
2. The page shell determines whether that key maps to a signer identity that can still claim a username.
3. If eligible, the page shows a prominent near-top `Choose your username` CTA that links to the existing profile update page for that identity.
4. The user follows the CTA and completes the existing signed username-claim flow.
5. On later page loads, once the claim has been spent, the shared CTA is no longer shown.

## Success Criteria
- A user with a stored browser key and no username sees the CTA near the top of every normal page.
- A user without a stored key, or with a spent/ineligible signer identity, does not see the CTA.
- The CTA routes to the existing `/profiles/<identity-slug>/update` flow for the eligible signer identity.
- The CTA copy is concise, action-oriented, and works for both first-time and returning no-username users.
- The feature stays narrow: shared-page discoverability improves without creating a new onboarding flow or changing username-claim policy.
