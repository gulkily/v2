## Problem
The shared header currently hides the `My profile` nav item until browser JavaScript derives the current profile target, which causes the primary nav to shift after page load. The next slice should keep the existing `My profile` affordance but make the nav layout stable before JavaScript enhancement runs.

## User Stories
- As a returning user, I want the primary navigation to stay visually stable while the page loads so that the header does not jump.
- As a signed user, I want `My profile` to remain easy to find in the main nav so that the account entry point still feels persistent.
- As a user without a stored signing key, I want the shared nav to remain coherent so that a reserved `My profile` slot does not feel broken or misleading.
- As a maintainer, I want this fix to reuse the existing shared header and browser profile-target enhancement path so that the slice stays narrow.

## Core Requirements
- The slice must eliminate the visible layout shift caused by revealing `My profile` only after page-load JavaScript runs.
- The slice must preserve the existing `My profile` entry point in the shared primary navigation rather than moving it to a new surface.
- The slice must keep the existing browser-derived profile target behavior for users whose current profile href is only known client-side.
- The slice must keep the shared nav understandable for users who do not have a current profile target available.
- The slice must avoid turning this polish fix into a broader authentication, account-hub, or site-navigation redesign.

## Shared Component Inventory
- Existing shared primary nav in `forum_web/templates.py`: extend this canonical nav contract because the problem is in the current header behavior, not a missing navigation surface.
- Existing shared page shell in `render_page(...)`: reuse as the common place where the nav and `profile_nav.js` are loaded across pages.
- Existing browser profile enhancement asset `profile_nav.js`: reuse and narrow its role to enriching the stable nav slot with the final href or count rather than inserting the nav item itself.
- Existing canonical profile routes `/profiles/<identity-slug>` and related profile-led account pages: preserve unchanged because this slice is about rendering stability, not changing profile destinations.

## Simple User Flow
1. A user loads any normal page in the app.
2. The shared header renders a stable `My profile` nav slot immediately, without shifting the nav row later.
3. If browser-held identity data is available, the existing client-side enhancement updates that slot with the correct destination or count.
4. The user selects `My profile` and reaches the same canonical profile-led account surface as before.

## Success Criteria
- Loading a normal page no longer causes the shared nav to shift when `My profile` becomes available.
- The primary navigation still includes a clear `My profile` entry point in the same shared location.
- Users with browser-resolved profile targets still reach the canonical profile route they used before.
- The fix stays scoped to stable nav rendering and enhancement behavior rather than introducing a broader account-surface redesign.
