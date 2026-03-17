## Problem
Merged identities already resolve to one canonical profile, but public profile reads and attribution links are still keyed by canonical identity slug rather than by the latest current username. The next slice should add the smallest useful username-first public profile route and link behavior for merged identities without pulling in username approval policy, collision adjudication, or historical alias routing.

## User Stories
- As a reader, I want to open a merged profile by current username so that I can find a person by the name they present publicly.
- As a user with merged identities, I want one username-based public profile page so that my joined profile is easier to reach than a fingerprint-derived identity slug.
- As a reader, I want profile links under posts and moderation attribution to land on the right public page so that username-first profiles are reachable through normal browsing flows.
- As a reader, I want the joined page to show all usernames in the merged set when they still differ so that the public profile reflects unresolved naming differences honestly.
- As a maintainer, I want username-based profile resolution to stay conservative so that this slice does not implicitly decide username ownership or collision policy.

## Core Requirements
- The slice must add a public `/user/<username>` read route keyed by the latest current username rather than by historical aliases.
- The route must resolve only when the username maps cleanly to one resolved identity set under the current visible repository state.
- The username-based page must reuse the existing resolved profile model for merged identities rather than creating a parallel account/profile representation.
- Existing attribution links must prefer the username-based route when one unambiguous latest current username exists for the resolved profile, and otherwise fall back to the canonical identity-based route.
- The joined page must expose all usernames in the merged set when no single unified name has been explicitly chosen.
- The slice must avoid username approval workflows, moderator adjudication of username ownership, chooser pages for ambiguous collisions, or permanent old-username aliases after rename.

## Shared Component Inventory
- Existing resolved profile model in `forum_web/profiles.py`: extend the canonical profile-summary derivation rather than inventing a second joined-profile read model, because merged identities already resolve there.
- Existing web profile surface `/profiles/<identity-slug>`: reuse as the canonical identity-keyed read page and extend its profile data contract as needed, because `/user/<username>` should land on the same underlying joined profile information.
- Existing attribution surfaces on posts and moderation records: extend these canonical links so they prefer `/user/<username>` only when resolution is unambiguous, because readers normally discover profiles through attribution before direct URL entry.
- Existing profile-update record family: reuse as the canonical source of latest current usernames and merged-set username history, because it already records visible user-chosen names.
- Existing identity-resolution and approved-merge model: reuse as the authority for which identities belong to one joined profile, because the feature depends on resolved identity sets rather than raw username overlap.
- New public username route `/user/<username>`: add one focused read surface because no existing route lets readers open the resolved profile directly by username.

## Simple User Flow
1. A user merges identities through the existing merge workflow and has visible current usernames in the profile-update history.
2. A reader visits `/user/<username>` using the latest current username.
3. If that username maps unambiguously to one resolved identity set, the system renders the joined profile for that merged account.
4. The page shows the existing resolved profile information and includes all usernames in the merged set when they still differ.
5. When the same profile is reached from post or moderation attribution, links prefer `/user/<username>` only when that username mapping is unambiguous; otherwise they keep using `/profiles/<identity-slug>`.
6. If the username does not map cleanly to one resolved identity set, the route fails conservatively instead of guessing.

## Success Criteria
- A latest current username that maps to one resolved identity set loads a joined public profile at `/user/<username>`.
- The rendered page reflects the same underlying merged profile readers would reach through the canonical identity-based profile route.
- Post and moderation attribution links prefer the username-based route when one unambiguous latest current username exists, and otherwise continue to land on the correct identity-based profile.
- When merged members still imply multiple usernames, the joined page shows those usernames instead of pretending one was chosen automatically.
- Old usernames do not continue resolving after a later rename unless they are still the latest current username.
- Ambiguous username matches fail conservatively rather than selecting a profile or introducing a chooser workflow.
