## Problem
The product now allows username updates only for profiles that are currently eligible under repository-state rules, but the public profile and merge-management pages still show `update username` actions even when the viewed profile cannot successfully use them. The next slice should hide those ineligible affordances so the main UI stops advertising actions that will deterministically fail.

## User Stories
- As a user who is not currently eligible to update a username, I want the profile UI to stop showing `update username` so that I do not click into a dead end.
- As a user who is currently eligible to update a username, I want the action to remain visible so that I can still find the allowed flow.
- As a reader or reviewer, I want public profile pages to reflect the one-claim policy cleanly so that the visible controls match the actual allowed actions.
- As a future implementer, I want the spent-claim visibility rule to be explicit so the same profile state produces the same affordances across implementations.

## Core Requirements
- The system must hide the `update username` affordance whenever the viewed profile is not currently eligible for a username update under repository-state rules.
- The system must continue showing the `update username` affordance only when the viewed profile is currently eligible for a username update.
- The hide/show rule must be derived from current visible repository state, not browser-local state, cookies, or local-key detection.
- The slice must keep the existing backend eligibility/validation rules unchanged; this is a UI/read-surface affordance change, not a new write-policy change.
- The slice must avoid adding disabled controls, new settings pages, or alternative explanatory workflows on the public profile surfaces.

## Shared Component Inventory
- Existing profile page surface: extend `/profiles/<identity-slug>` because it currently shows the main `update username` action in the profile action cluster.
- Existing merge-management surface: extend `/profiles/<identity-slug>/merge` because it currently repeats the same `update username` affordance in its local navigation.
- Existing read-model/profile context: extend the current profile summary or related read helper rather than inventing a second ownership model, because the needed state is only whether the viewed profile is currently eligible to update its username.
- Existing update page and `/api/update_profile` contract: leave them unchanged, because the feature is about whether to advertise the action, not about changing the signed submission flow.

## Simple User Flow
1. A user visits a profile or merge-management page for a profile that is currently eligible to update its username.
2. The UI shows `update username` as the path into the one-time claim flow.
3. After repository state changes so that the viewed profile is no longer eligible, the same profile and merge-management pages are rendered again.
4. The UI no longer shows `update username` for that ineligible profile.
5. Other profiles that remain eligible still show the affordance on their own pages.

## Success Criteria
- A profile page hides `update username` whenever the viewed profile is not eligible to update its username.
- The merge-management page hides the same affordance under the same ineligible condition.
- Profiles that remain eligible still show `update username`.
- The hide/show behavior is deterministic from repository state and does not depend on browser-local state.
- The slice reduces dead-end navigation without changing the existing backend eligibility rules.
