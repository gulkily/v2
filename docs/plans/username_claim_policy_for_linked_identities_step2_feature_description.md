## Problem
Usernames currently behave like editable profile updates, which becomes confusing once multiple linked identities resolve to one public profile. The next slice should restrict username claims to one claim per key pair while keeping merged-profile reads deterministic and auditable.

## User Stories
- As a signed user, I want my key to establish a username once so that I do not accidentally churn names through repeated edits.
- As a user with linked identities, I want the merged profile to show one deterministic current username so that readers see a stable public label.
- As a reviewer, I want username claims to remain signer-anchored and auditable so that each visible claim can be traced to one concrete key.
- As a future implementer, I want the username winner rule across linked identities to be explicit so that other implementations reproduce the same visible profile state.

## Core Requirements
- Each concrete signer identity/key pair may publish at most one accepted username/display-name claim.
- The system must reject later username-claim attempts from the same signer identity after its first accepted claim is visible.
- Resolved profile reads must continue to show one deterministic current username across linked identities even when multiple member identities each have one claim.
- The winner rule across linked identities must be explicit and stable under the current visible repository state.
- The slice must avoid adding composite-profile write authority, cookie/session ownership state, or broader account-settings behavior.

## Shared Component Inventory
- Existing API write surface: extend `/api/update_profile` validation because it already accepts signer-anchored username/display-name claims and should remain the canonical write contract.
- Existing profile-update record model: reuse the current signed record family rather than inventing a second username-claim format, because the main change is claim policy, not storage shape.
- Existing web profile-update surface: extend `/profiles/<identity-slug>/update` to reflect the new one-claim policy and resulting failure states; no new page is needed.
- Existing profile read surfaces: reuse `/profiles/<identity-slug>`, `/user/<username>`, and `/api/get_profile` because they already resolve the winning visible display name across linked identities.
- Existing attribution surfaces: keep thread, post, and moderation author labels on the same read model so the chosen winning username remains consistent everywhere.

## Simple User Flow
1. A user opens the username-update page for one signer identity and submits an initial signed username claim.
2. The server accepts that first visible claim for that signer identity and stores it as the canonical profile-update record.
3. If the same signer identity later attempts another username claim, the server rejects it under the one-claim policy.
4. If multiple linked identities each have one accepted claim, the resolved profile read model applies the deterministic winner rule and shows one current username on profile and attribution surfaces.
5. Readers continue to see one stable username for the merged profile under the current visible repository state.

## Success Criteria
- A signer identity can establish one initial username claim through the existing signed profile-update flow.
- A second username-claim attempt from the same signer identity is rejected deterministically.
- Merged-profile read surfaces still return one deterministic current username when linked identities each have at most one accepted claim.
- `/profiles/<identity-slug>`, `/user/<username>`, and existing attribution surfaces stay aligned on the same visible winning username.
- The policy is narrow enough to reduce rename ambiguity without introducing resolved-profile-level write authority.
