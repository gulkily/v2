## Problem
Users can reach their own profile via `?self=1`, but that page does not currently give them a direct path to username setup even when the existing username-update flow is available to that profile. The next slice should add that self-serve link on `My profile` without exposing it on profiles that are not eligible to use the flow.

## User Stories
- As a user viewing my own profile, I want a direct link to username setup so that account-related actions are discoverable from `My profile`.
- As a user whose profile is eligible to claim or update a username, I want that link to appear only when I can actually use it so that the page does not send me into a dead end.
- As a user viewing someone else’s profile, I do not want to see self-only account-management links so that public profile pages stay focused on public information.
- As a future implementer, I want the self-profile visibility rule to be explicit so the same route and profile state render the same affordances consistently.

## Core Requirements
- The self-profile page (`/profiles/<identity-slug>?self=1`) must show a direct link to the existing username setup flow only when that profile is currently eligible to update its username.
- The same username-settings link must remain hidden on self-profile pages when the profile is not eligible to update its username.
- The link must remain absent from normal public profile views that are not rendered as the self-profile route.
- The eligibility rule must reuse current repository-state username-update logic rather than browser-local state, local-key presence, or a new policy.
- The slice must reuse the existing `/profiles/<identity-slug>/update` destination rather than introducing a new settings page or write contract.

## Shared Component Inventory
- Existing self-profile surface: extend `/profiles/<identity-slug>?self=1` because this is the requested destination and already serves as the user-facing `My profile` page.
- Existing public profile surface: reuse the same profile page rendering path, but keep the new affordance scoped to self-profile rendering so public profile pages do not gain account-only controls.
- Existing username eligibility logic: reuse the current repository-state rule that determines whether a profile can still update its username.
- Existing username update flow: reuse `/profiles/<identity-slug>/update` because the feature is about discoverability from `My profile`, not a new settings destination.

## Simple User Flow
1. A user opens `My profile` on `/profiles/<identity-slug>?self=1`.
2. The page checks whether that profile is currently eligible for the existing username-update flow.
3. If the profile is eligible, the page shows a direct username-settings link.
4. The user selects that link and reaches the existing username update page.
5. If the same profile is later no longer eligible, `My profile` renders again without that link.

## Success Criteria
- Eligible self-profile pages show a clear direct link to the existing username setup flow.
- Ineligible self-profile pages do not show that link.
- Non-self public profile pages do not show the self-only username-settings link.
- The link target stays the existing `/profiles/<identity-slug>/update` route.
- Visibility stays deterministic from current repository state rather than browser-local conditions.
