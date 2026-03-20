## Problem
The account merge feature currently feels unfinished and confusing, but it is already wired into multiple profile, navigation, page, asset, and API surfaces. The next slice should mothball it behind one default-off feature flag so production users do not encounter it while the implementation remains available for future work.

## User Stories
- As a product manager, I want the account merge feature off by default so that unfinished merge flows do not ship to normal users.
- As a developer, I want one shared feature flag controlling merge-related surfaces so that local testing and future development stay predictable.
- As a signed user, I want merge-related links, suggestions, and notifications to disappear together so that the product does not feel partially broken.
- As a maintainer, I want existing merge records and core identity resolution to remain intact so that mothballing does not become a destructive rollback.

## Core Requirements
- The product must use one shared feature flag, off by default, to control merge-related release visibility.
- When the flag is off, merge-specific user-facing web surfaces and merge-related navigation affordances must not appear.
- When the flag is off, merge-specific direct routes and APIs must not act like an available product feature.
- Existing merge data and non-merge profile/read behavior must continue to work without schema changes or record deletion.
- When the flag is on, the current merge feature should behave as it does today.

## Shared Component Inventory
- Existing profile page surface `/profiles/<identity-slug>`: extend the canonical profile action area and self-merge suggestion area to respect the shared merge flag because these are the primary merge entry points.
- Existing merge management page `/profiles/<identity-slug>/merge` and merge action page `/profiles/<identity-slug>/merge/action`: extend these existing routes to be flag-aware rather than creating alternate hidden versions.
- Existing shared profile navigation asset `profile_nav.js`: extend it to suppress merge-related notification behavior when the feature is off because the nav currently redirects users into merge management.
- Existing merge suggestion asset `profile_merge_suggestion.js`: extend it to follow the same shared flag because it powers one of the merge feature’s visible profile affordances.
- Existing merge APIs `/api/get_merge_management` and `/api/merge_request`: extend these canonical endpoints to follow the same release posture because direct access should not bypass the mothball state.
- Existing merge-aware identity/read model behavior: reuse unchanged because the goal is release gating of the unfinished feature, not removal of underlying historical records or resolution logic.

## Simple User Flow
1. The operator runs the product with the merge feature flag left at its default value.
2. A signed user browses profiles, nav, and related account pages.
3. The UI does not show merge suggestions, merge links, merge notifications, or merge pages as an available feature.
4. A developer who wants to continue merge work enables the flag locally and regains the current merge feature behavior.

## Success Criteria
- With the flag off, normal UI flows no longer expose merge suggestions, merge links, merge notifications, merge pages, or merge actions.
- With the flag off, direct merge endpoints no longer behave like an available feature surface.
- With the flag on, the current merge feature remains reachable through the existing routes and affordances.
- Non-merge profile, account, and identity read behavior remains unchanged in both flag states.
