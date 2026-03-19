## Problem
Eligible new users can still claim a username, but that one-time opportunity is currently easy to miss because it only appears as a normal page action. The next slice should make the initial username-claim opportunity more visible on eligible profile pages without reintroducing dead-end UI for ineligible profiles.

## User Stories
- As a new user who has not chosen a username yet, I want to see clearly from my profile header that I can still claim one so that I discover the feature without hunting through page actions.
- As a user who has already spent the claim, I do not want to see the same prominent callout so that the profile header does not advertise an unavailable action.
- As a reader or reviewer, I want the profile header messaging to match repository-state eligibility so that visible guidance stays consistent with the actual allowed action.
- As a future implementer, I want the visibility rule for this header callout to be explicit so the same profile state renders the same guidance across implementations.

## Core Requirements
- The profile page must show a prominent username-claim callout in or near the page header only when the viewed profile is currently eligible to update its username.
- The callout must remain hidden for profiles that are not eligible to update their username.
- The visibility rule must be derived from current visible repository state, reusing the existing eligibility logic rather than browser-local state or session detection.
- The slice must reuse the existing update-username flow as the call-to-action target rather than introducing a new onboarding page or new write contract.
- The slice must avoid cluttering ineligible profile headers with disabled, stale, or explanatory dead-end controls.

## Shared Component Inventory
- Existing profile page surface: extend `/profiles/<identity-slug>` because this is where new users currently land and where the profile hero/header is already rendered.
- Existing eligibility logic: reuse the current repository-state eligibility rule that already governs whether `update username` should be shown on read surfaces.
- Existing update flow: reuse `/profiles/<identity-slug>/update` as the destination because the feature is about discoverability, not a new write path.
- Existing merge-management and other read surfaces: leave them unchanged for this slice unless they already depend on the same shared header/profile state; the primary visibility improvement belongs on the profile page.

## Simple User Flow
1. A new user visits an eligible profile page that has not yet spent its one username claim.
2. The profile header prominently tells the user that a one-time username claim is available and links to the existing update page.
3. The user follows that call-to-action into the existing signed username-claim flow.
4. After the username claim is accepted, the profile is rendered again from repository state.
5. The prominent header callout is no longer shown on that now-ineligible profile.

## Success Criteria
- Eligible profiles show a clearly visible header-level invitation to claim a username.
- Ineligible profiles do not show that prominent invitation.
- The callout links into the existing `/profiles/<identity-slug>/update` flow rather than inventing a new path.
- The visibility behavior is deterministic from repository state and stays aligned with the existing eligibility rule.
- The slice improves discoverability for new users without undoing the recent hiding of dead-end update actions.
