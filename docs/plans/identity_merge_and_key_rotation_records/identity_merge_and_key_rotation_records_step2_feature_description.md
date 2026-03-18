## Problem
The forum can now bootstrap one key-backed identity and expose a profile for it, but the current identity layer still assumes `one key == one identity`. The next slice should add the smallest useful merge and rotation model so a user can move to a new key or link two existing identities without losing profile continuity, while keeping the loop focused on signed identity-link records and deterministic identity resolution rather than display-name editing, moderator trust policy, or browser UX.

## User Stories
- As a signed user, I want to rotate to a new key without fragmenting my profile into two unrelated identities.
- As a user with two existing key-backed identities, I want to link them so readers can resolve one logical profile across both.
- As a reader, I want old and new signed posts to resolve to the same profile when a valid merge or rotation record exists.
- As a future backend implementer, I want identity-link resolution to be explicit and deterministic so other implementations can reproduce the same merged profile output.
- As a reviewer, I want merge and rotation intent stored as canonical signed text records in git rather than hidden mutable aliases.

## Core Requirements
- The slice must define one canonical signed identity-link record family stored separately from posts and bootstrap records, likely under `records/identity-links/`.
- The slice must support at least two link actions: `rotate_key` and `merge_identity`.
- The slice must keep the current per-key bootstrap model in place; each key may still have its own bootstrap material, and identity-link records sit on top of that rather than replacing it.
- The slice must introduce a deterministic identity-resolution pass that maps visible bootstrap keys and visible identity-link records to one resolved logical identity.
- The slice must define a deterministic canonical identity selection rule for a resolved linked set and apply it consistently in profile reads and profile URLs.
- The slice must allow `get_profile` and the web profile view to accept any member identity or key-backed alias in a resolved set and return the same resolved logical profile.
- The slice must update signed post attribution and moderation attribution to resolve through the new identity-resolution layer instead of assuming `identity_id == fingerprint-derived ID`.
- The slice must keep the write path API/CLI-first. A browser flow for merge or key-rotation management is out of scope for this loop.
- The slice must avoid display-name editing, moderator-trusted merge assertions, cross-repo conflict mediation, federation merge policy, or anonymous-identity changes.

## Deterministic Resolution Rules
- `rotate_key` is a signed assertion from an already visible key-backed identity that introduces a new public key into the same logical identity set.
- `merge_identity` is a signed assertion linking two already visible identities; to keep this slice conservative and deterministic, the merge only becomes active when reciprocal visible merge assertions exist between the two identities.
- Resolved identity membership is derived only from visible bootstrap records plus visible active identity-link records.
- The canonical logical identity for a resolved set is the lexicographically smallest member `Identity-ID`.
- Older non-canonical member profile URLs must still resolve to the same logical profile summary rather than breaking.

## Shared Component Inventory
- Existing UI surfaces: reuse the current profile page and post/moderation attribution links, updating them to resolve through canonical linked identities.
- Existing API surfaces: add one identity-link write contract and update `get_profile` so it returns a resolved profile summary rather than a single-fingerprint-only view.
- Existing data surfaces: keep `records/identity/` bootstraps and add canonical signed identity-link records plus detached signature/public-key sidecars.
- Existing backend surfaces: build on current detached-signature verification, identity bootstrap loading, and git-backed write helpers so link records are verified, stored, and committed through the same machinery.

## Simple User Flow
1. A user with an existing key-backed identity submits a signed `rotate_key` record that references a new public key.
2. The server verifies the signature, stores the canonical identity-link record, and commits it to git.
3. The user later signs posts with the new key; the current bootstrap flow may still create bootstrap material for that key, but the identity-resolution layer maps both keys to one logical identity.
4. Separately, two already visible identities can submit reciprocal signed `merge_identity` records.
5. Once both reciprocal merge records are visible, the server resolves both identities into one logical profile set with one canonical identity ID.
6. A reader requests `get_profile` or visits `/profiles/<identity-slug>` using either the old or new member identity, and the server returns the same resolved profile summary.

## Success Criteria
- A valid signed `rotate_key` record causes posts signed by the new key to resolve to the same logical profile as the old key.
- Reciprocal signed `merge_identity` records cause two existing key-backed identities to resolve to one logical profile.
- Identity-link records are stored as canonical text files with detached signatures and git commits.
- `get_profile` and the web profile view return deterministic resolved summaries for linked identities.
- Existing signed posts and moderation records still render with stable author attribution after the identity-resolution refactor.
- The merge/rotation behavior is precise enough to serve as fixture targets for later non-Python implementations.
