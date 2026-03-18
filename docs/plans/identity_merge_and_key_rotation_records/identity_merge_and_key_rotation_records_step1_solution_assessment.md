## Problem Statement
Choose the smallest useful way to introduce identity merge and key rotation after Loop 6, without turning the next loop into display-name editing, moderator-trust policy, federation conflict resolution, or a full rewrite of signed posting.

The current implementation still assumes `one key == one identity` in several important places:

- `Identity-ID` is derived directly from one fingerprint.
- signed posts derive `identity_id` directly from the attached public key.
- profile summaries assume one bootstrap, one signer fingerprint, and one public key.

So the next loop cannot be only "add one new record type." It needs a coherent identity-resolution layer.

### Option A: Add explicit signed identity-link records and a derived identity-resolution layer
- Pros:
  - Addresses the real architectural gap directly instead of hiding it behind aliases.
  - Fits the git-backed, append-only model by expressing merge and rotation as explicit signed records rather than mutation.
  - Lets the system resolve many fingerprints to one logical identity while keeping current signed posts and bootstraps useful.
  - Creates a stable foundation for later profile updates, because display names and other profile fields can attach to a resolved logical identity instead of a single key.
  - Matches the architecture notes that merges and key rotation should happen through signed links between keys.
- Cons:
  - Requires a meaningful refactor of the identity read model rather than a narrow additive change.
  - Needs a first-cut rule for canonical identity selection and profile URL stability after a merge.
  - Needs deterministic behavior when conflicting or partial merge/rotation records appear.

### Option B: Keep fingerprint-derived identities and add alias records or redirects only
- Pros:
  - Smaller immediate implementation surface.
  - Could add basic "this key maps to that profile" behavior quickly.
  - Might preserve existing profile URLs with less reader churn in the short term.
- Cons:
  - Leaves the core `one key == one identity` model in place and layers indirection on top of it.
  - Makes later profile derivation, moderation attribution, and post rendering more awkward because some code will still think in per-key identities while other code thinks in merged identities.
  - Turns key rotation into chained aliases instead of a clear canonical resolution model.
  - Increases the chance that Loop 14 has to be partially redone later.

### Option C: Represent merge and rotation by rewriting bootstrap records or replacing the identity anchor in place
- Pros:
  - Superficially simple if viewed only as "swap old key for new key."
  - Avoids building a separate identity-link record family right away.
- Cons:
  - Conflicts with the append-only, auditable, git-native design already used for posts and moderation.
  - Makes history and fork behavior harder to reason about, because identity evolution becomes implicit mutation instead of explicit signed intent.
  - Does not map cleanly to "many keys, one logical identity," which is already a stated requirement.

## Recommendation
Recommend Option A: add explicit signed identity-link records and a derived identity-resolution layer.

This is the smallest coherent slice that actually solves the problem the current implementation has. The loop should stay strict about boundaries:

- Define one canonical record family for identity links, covering at least key rotation and identity merge.
- Introduce a deterministic identity-resolution pass that maps fingerprints and bootstrap records to one canonical logical identity.
- Choose one stable canonical identity selection rule for merged identities and use it consistently in profile URLs and read surfaces.
- Update post/profile/moderation attribution to resolve through that layer instead of assuming `identity_id == fingerprint-derived ID`.
- Add a write path for merge/rotation records, but keep it API/CLI-first rather than adding browser UX in the same loop.
- Leave display-name editing, moderator-trusted merge assertions, conflict mediation across divergent repos, and richer identity UI for later loops.

That gives the project a real identity model instead of a single-key placeholder. A user can rotate to a new key, two keys can be linked into one logical identity, and readers can still resolve a stable profile from repository-backed records. The cost is that this loop must deliberately refactor identity resolution instead of treating merge as a thin alias layer.
