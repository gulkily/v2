## Problem
The forum can now resolve multiple linked keys or sessions to one logical identity, but that identity still renders with fingerprint-derived labels instead of a user-chosen name. The next slice should add the smallest useful profile-update model so a user can publish a username/display name that follows the resolved identity across profile reads and signed attribution without reopening merge semantics or expanding into full profile management.

## User Stories
- As a signed user, I want to change my username/display name so that my profile shows a human-readable identity instead of only a fingerprint-derived label.
- As a user with multiple linked keys or sessions, I want one profile name to apply across the resolved identity so that readers see one coherent account after consolidation.
- As a reader, I want profile pages and signed attribution to show the same current display name so that authorship is understandable across posts and moderation actions.
- As a future backend implementer, I want profile-update behavior to be explicit and deterministic so other implementations can reproduce the same visible profile state.
- As a reviewer, I want profile updates stored as signed repository records so that name changes remain auditable instead of becoming hidden mutable account state.

## Core Requirements
- The slice must define one canonical signed profile-update record family separate from bootstrap and identity-link records.
- The slice must support the minimal profile-update action of setting or replacing the current username/display name for a resolved logical identity.
- The slice must resolve profile updates through the existing linked-identity model so any member identity in a resolved set returns the same current display name on profile reads.
- The slice must preserve a deterministic fallback label when no visible profile-update record exists yet.
- The slice must avoid avatars, bios, moderator-assigned labels, per-post pseudonyms, merge-policy changes, or browser profile-management UX.

## Shared Component Inventory
- Existing API profile surface: extend `/api/get_profile?identity_id=<identity-id>` so the canonical profile summary includes the current display name while keeping the resolved identity behavior already introduced in Loop 14.
- Existing web profile surface: extend `/profiles/<identity-slug>` so the canonical profile page shows the current display name for the resolved identity rather than only the fingerprint shorthand.
- Existing attribution surfaces: extend signed author and moderator links on thread, post, and moderation pages to prefer the current display name while reusing the same canonical profile target they already link to.
- Existing API discovery surface: extend `/api/` so the available-command list includes the new profile-update write route.
- New write surface: add one API/CLI-first profile-update command because current write routes cover posts, moderation, and identity links but not profile metadata changes.

## Simple User Flow
1. If needed, the user first links multiple keys or sessions through the existing identity-link model so they resolve to one logical identity.
2. The user submits a signed profile update that sets a new username/display name for that identity.
3. The server verifies the signed request, stores the canonical profile-update record, and makes it part of visible repository state.
4. A reader requests `get_profile` or visits the profile page using any member identity in the resolved set.
5. The system returns the same resolved profile with the current display name and uses that name in signed attribution surfaces.

## Success Criteria
- A valid signed profile update causes `/api/get_profile` and `/profiles/<identity-slug>` to show the same current display name for the resolved identity.
- The same display name appears when the profile is requested through any linked member identity alias in the resolved set.
- Signed post and moderation attribution surfaces prefer the current display name while keeping canonical profile links stable.
- When no profile-update record exists, profile and attribution reads still fall back deterministically to the current fingerprint-derived label.
- Profile-update behavior is specific enough to serve as a deterministic fixture target for later non-Python implementations.
