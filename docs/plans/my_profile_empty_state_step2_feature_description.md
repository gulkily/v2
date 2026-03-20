## Problem
The shared `My profile` navigation can already send a signed user to `/profiles/<identity-slug>` before that identity has published any visible post or profile update. In that first-visit state, the route currently falls through to the generic missing-record page instead of explaining that the profile exists as a personal destination but has not been published yet.

## User Stories
- As a brand new signed user, I want `My profile` to open a meaningful page even before I post so that the account entry point does not feel broken.
- As a brand new signed user, I want the page to explain why my profile looks empty and what I can do next so that I understand how to make the profile become visible.
- As a returning signed user, I want `My profile` to keep using the same canonical route so that the destination stays predictable before and after I publish activity.
- As a maintainer, I want this improvement to reuse the existing profile-led account surface so that the slice stays narrow and does not create a second account hub.

## Core Requirements
- The slice must replace the generic missing-resource experience for first-time `My profile` visits with a profile-aware empty state.
- The empty state must live on the existing canonical profile route rather than redirecting to a separate setup destination.
- The page must explain that no signed posts or profile updates are published yet and present at least one clear next action.
- The slice must preserve the current published-profile behavior once visible profile data exists.
- The slice must avoid turning this fix into a broader onboarding, account-management, or identity-model redesign.

## Shared Component Inventory
- Existing canonical profile route `/profiles/<identity-slug>`: extend this canonical surface because it is already the destination behind `My profile` and should remain the stable account entry point.
- Existing shared page shell in `render_page(...)`: reuse so the new empty state inherits the standard header, nav, and page framing instead of creating a one-off layout.
- Existing shared `My profile` navigation and `profile_nav.js` enhancement path: reuse unchanged because the problem is the landing-state behavior after navigation resolves, not how the nav target is discovered.
- Existing generic missing-resource page in `forum_web/web.py`: do not reuse as the final user-facing result for this case because it describes an unknown record rather than an unpublished self-profile state.
- Existing profile-led actions such as posting, username update, and merge management: reuse only where they already make sense, without introducing a new account hub or duplicate setup flow.

## Simple User Flow
1. A brand new signed user selects `My profile` from the shared navigation.
2. The app opens the canonical `/profiles/<identity-slug>` route for that identity.
3. Because the user has not published any visible signed activity yet, the page renders a profile-specific empty state instead of the generic missing-record message.
4. The page explains the unpublished state and points the user to the smallest useful next action.
5. After the user publishes qualifying activity, the same route renders the normal profile view.

## Success Criteria
- A first-time signed user who opens `My profile` no longer sees “This record could not be located” for the pre-publication case.
- The user can understand from the page why their profile is empty and what to do next.
- `My profile` continues to resolve to the same canonical `/profiles/<identity-slug>` route before and after the user publishes activity.
- Published profiles continue to render through the existing profile view without regression into a separate onboarding surface.
