# Username Collision Working Notes

Purpose: a collaborative draft for designing username choice, collision handling, merge approval, and related recovery/revocation behavior.

Status: working notes, not yet a committed product policy.

## Current System Baseline

These notes should stay grounded in the current repo behavior:

- usernames/display names come from signed profile updates
- identities are key-backed
- identities can be linked through merge/key-rotation records
- same-name overlap can already be used as a merge suggestion
- merge requests currently require explicit approval and do not auto-merge on username overlap
- public `/user/<username>` routing is conservative and should not guess when a username is ambiguous

## Primary Goal

Make username selection and conflict handling feel seamless to normal users without making mistaken merges or username hijacking too easy.

## Settled Decisions

### Canonical Username Root

For each current username token, there should be one canonical username "root" identity.

- the canonical root is the identity or merged identity set whose username claim appears first in git commit chronology
- that root represents the username publicly for now
- if the root later becomes part of a merged identity set, the canonical username root should refer to that whole linked set rather than only one raw key identity
- other unmerged identities using the same username should not take over the canonical route automatically
- the canonical root gets the main `/user/<username>` resolution
- non-root identities with the same username should be shown as `other users with this name`
- if a later merge links one of those other identities into the root set, it should stop being listed as "other" and become part of the root set
- the deciding event is the first visible signed profile update that claims the username, ordered by git commit chronology rather than by payload timestamp
- in the normal case, no separate tie-break is needed because repository commit chronology is already sequential
- if history is rewritten or imported, the resulting repository chronology becomes the new source of truth and all derived username-root decisions should follow it

### Merge Request Confidence

- username overlap alone is sufficient for auto-issued merge requests for now
- stronger corroborating evidence may be added later, but is not required for the first version

### Merge Scope

- one approved merge should attach the incoming identity to the whole resolved set
- later identity resolution should continue using the existing graph rules

### Notifications

- a full inbox is not required for the first version
- merge-request and related account notifications should attach to the `My profile` navigation entry
- that nav entry should surface pending merge approvals and other username/account actions that need attention

### Merge Revocation

- use a one-sided append-only `revoke_merge` style record
- revocation takes effect immediately
- no extra approval is required for the first version
- the revocation record should reference whichever prior merge approval or active edge is simplest to implement while remaining deterministic
- revocation deactivates a specific approved merge edge
- once revoked, the identity graph is recomputed from the remaining active edges using the existing rules
- canonical username-root ownership is recalculated using the same existing rules as before
- any identities no longer attached to the root set after recomputing the graph should appear in the `other users with this name` section
- profile updates made during the merged period remain historical facts; current display state follows whatever identities remain connected after recomputing the graph
- posts and attribution should behave the same way as other current read surfaces: recompute from the current identity graph and show the current result without special-case backfill rules

### Cache Direction

- relationships between user identities should be cached in the SQLite index
- identity-resolution and username-root derivations are good cache candidates because they are derived, query-heavy, and rebuildable from canonical repository records
- one SQLite file is the default direction unless there is a concrete rebuild, contention, or operational reason to split caches later

## Scenarios

### 1. Same user, multiple devices

This is likely the most common collision case.

- if a new device starts using a username already used by the same logical person, the system should recognize this as a likely self-merge case
- the new device should be able to issue a merge request automatically or near-automatically
- the user should see a notification on their other signed-in devices
- one confirmation should be enough to merge the new key into the whole existing merged identity set

### 2. Multiple keys that really are one shared identity

This is similar to the multi-device case, except the model is shared identity rather than one person with one device per key.

- the workflow should be basically the same as multi-device linking
- one approved merge should join the incoming key to the entire merged set
- one-sided revocation should remain available for mistaken merges or later disagreement

### 3. New user wants a username already used by someone else

This is the main true collision case.

- the new user should get a smooth explanation before finalizing the conflicting username
- the system should avoid hard rejection whenever possible
- the system should avoid forcing unrelated users into merge-like flows
- accept the user's preferred input whenever possible, but treat the public routing/display consequences separately from the stored preference
- show all other conflicting identities as `other users with this name`
- reserve merge suggestions for cases where there is already evidence that the identities may belong together
- do not treat "same chosen username" alone as enough reason to open an aggressive merge flow

## Other Scenarios To Consider

### 4. Mistaken merge between unrelated users

Possible causes:

- same common username
- shared device
- weak evidence and rushed approval
- moderator error

Questions:

- how do we preserve auditability while restoring separate public profiles

### 5. Compromised key requests merge into an existing identity

Risk:

- an attacker who controls one key may try to merge into a trusted username set

### 6. Rename collision after merge

Example:

- a merged set already exists
- one member changes the current username to a name already used by another unrelated set

Resolution:

- do not block the rename
- allow the rename and keep applying the same canonical-root and `other users with this name` rules
- no extra collision rule is needed beyond the existing public-routing behavior

### 7. Historical-name squatting

Example:

- a user abandons a username
- someone else quickly takes it to capture recognition or confuse readers

Resolution:

- no cooldown for now
- no special protection tier for notable or long-held usernames in the first version
- continue relying on the same current-username root and visible-others behavior rather than adding reservation rules

### 8. Moderator-assisted identity dispute

Example:

- two users both claim a username lineage
- neither side wants to merge
- a moderator needs tools short of forcing a merge

Resolution:

- no special moderator dispute marker in the first version
- no username freeze mechanism in the first version
- moderators can continue using the existing moderation model without adding new username-specific state

## Working Principles

- same username should be a suggestion signal, not automatic proof
- same-person multi-device linking should feel much easier than unrelated-user collision handling
- one approval should be enough to attach a new key to an already-merged set
- mistaken merges must have some recovery path
- public username routing should prefer one canonical root identity or root merged set per username
- other conflicting identities should be visible as `other users with this name`
- choosing a username should be easy, and the system should avoid rejecting input unless there is a strong safety reason
- when conflicts happen, prefer disambiguation and conservative routing over immediate rejection
- when in doubt, prefer the current graph-derived visible state over adding special-case username policy

## Questions For Next Iteration

- Should merge approvals show stronger warning language and more account-history evidence before the user confirms
  For example: should the approval UI show prior usernames, linked identities, first-seen chronology, recent posts, or a plain warning that merging affects the whole resolved set and may need later revocation if approved by mistake.
- Should the canonical username root always follow earliest claim in current repo history, even if that root later becomes inactive or clearly abandoned.
- Should a user be able to see why another identity appears under `other users with this name`, for example shared username history or chronology.
- Should auto-issued merge requests happen immediately on username match, or only after the new username claim is actually committed.
- Should there be an easy `not me` dismissal path for suggested self-merges so the same suggestion does not keep resurfacing.
- If one identity in a merged set changes usernames, should the rest of the set automatically inherit that current name unless later split by graph changes.
- When a merge is revoked, should the split-off identity keep seeing old merge notifications/history in the `My profile` area, or only current actionable items.
- Should `other users with this name` be ordered by repo chronology, recent activity, or something else.
- If a username has many unrelated claimants, should the UI cap or collapse the `other users with this name` list.
- Should duplicate-name situations affect posting attribution text, or only profile and navigation surfaces.
- Should cached identity and username graph data be recomputed synchronously on every relevant write, or allowed to lag briefly and self-heal on read.
- Should moderators get any extra visibility into username-root and merge-graph state for debugging, even if they do not get new powers.
- Should users be able to manually request merge even when there is no shared username overlap, or should the current flow stay username-driven only.
