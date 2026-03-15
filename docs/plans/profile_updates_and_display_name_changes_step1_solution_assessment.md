## Problem Statement
Choose the smallest useful way to let a user present one human-readable profile across already linked identities and change that profile's username/display name, without reopening merge semantics, overloading bootstrap records, or turning the next loop into full profile management.

### Option A: Add dedicated signed profile-update records resolved at the logical identity layer
- Pros:
  - Builds directly on the existing linked-identity model, so once multiple keys or sessions resolve to one logical identity they can share one visible profile name.
  - Keeps profile changes append-only and auditable as signed text records in git instead of hidden mutable account state.
  - Keeps identity-link records focused on merge and rotation intent rather than mixing identity resolution with profile metadata.
  - Leaves a clean path for later optional profile fields without changing how identities are linked.
- Cons:
  - Adds another canonical record family and another precedence rule for the current visible profile state.
  - Needs deterministic handling when different member identities in one linked set publish competing display-name updates.
  - Requires explicit fallback behavior when no profile-update record exists yet.

### Option B: Reuse bootstrap or identity-link records as the place where display names live
- Pros:
  - Smaller apparent surface area because it avoids a new profile-update record type.
  - Keeps profile labels close to identity anchors that already exist.
  - Might reuse more of the current write path shape with fewer new concepts.
- Cons:
  - Mixes stable identity/bootstrap intent with mutable profile metadata.
  - Fits poorly once identities are merged, because multiple bootstraps or link records may imply different names for the same resolved profile.
  - Pushes username changes toward rewriting, superseding, or overloading records that currently act as durable identity anchors.
  - Makes later profile expansion less clean because profile state is scattered across unrelated record families.

### Option C: Derive the visible username from posts or client/session-local preferences
- Pros:
  - Smallest immediate UX surface.
  - Avoids a new canonical profile record family in the short term.
  - Lets clients experiment with custom labels quickly.
- Cons:
  - Does not create one stable account-level name across merged identities.
  - Makes profile reads less deterministic because the visible label depends on post history or local client behavior.
  - Conflicts with the repository-backed design where canonical identity state should live in signed records.
  - Weakens attribution and moderation clarity because the same resolved identity can present different names in different contexts.

## Recommendation
Recommend Option A: add dedicated signed profile-update records resolved at the logical identity layer.

This is the smallest coherent slice now that linked identities already exist. The loop should stay strict about boundaries:

- Treat the existing identity-link model as the mechanism for consolidating multiple keys or sessions into one logical identity.
- Add one append-only profile-update record family for human-facing profile metadata, starting with display-name or username changes only.
- Resolve those updates through the canonical linked identity set so merged identities share one visible profile name.
- Keep deterministic fallback behavior when no profile-update record exists, using the current fingerprint-derived identity label.
- Leave avatars, bios, moderator-assigned labels, per-post pseudonyms, browser profile-management UX, and cross-repo conflict policy for later loops.

That gives the project a named profile layer without undoing earlier identity work: a user can consolidate activity through the existing link model, then apply one signed username/display-name update to the resolved identity readers already see. The tradeoff is one more record family and a small amount of deterministic precedence logic, but that is cleaner than mutating bootstrap records or making usernames depend on posts.
