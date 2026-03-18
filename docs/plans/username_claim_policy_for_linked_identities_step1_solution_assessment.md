## Problem Statement
Choose the simplest username-claim policy to avoid confusing composite-identity rename behavior while preserving a coherent user-facing account model.

### Option A: Allow one username claim per key pair
- Pros:
  - Smallest change from the current signer-anchored profile-update model.
  - Keeps authority easy to explain technically because each key may publish at most one username claim.
  - Avoids repeat rename churn from the same key.
- Cons:
  - Merged profiles can still accumulate multiple competing username claims from different linked keys.
  - The read model still needs a winner rule across linked identities, which stays surprising to users.
  - Does not fully match the product story of “my linked account has one username.”

### Option B: Allow one username claim per resolved profile
- Pros:
  - Best matches the user mental model that one linked account should have one username.
  - Eliminates repeated rename churn across merged identities, not just within one key.
  - Simplifies public behavior because a resolved profile can only establish one visible username claim.
- Cons:
  - Needs composite-profile authority rules for deciding which member key may make the initial claim.
  - Larger policy change because write validation must reason about resolved profiles, not only exact signer identities.
  - Harder to add incrementally if the current write contract stays strictly signer-anchored.

### Option C: Keep username claims editable for now and continue refining composite write authority
- Pros:
  - Most flexible long-term model.
  - Avoids locking in a restrictive policy before the broader account model is settled.
  - Lets later profile-management work support legitimate renames.
- Cons:
  - Leaves the current user experience confusing in the near term.
  - Requires more authority and UI work than the immediate problem likely deserves.
  - Keeps composite-identity write semantics exposed during a period when they are still awkward.

## Recommendation
Recommend Option A: allow one username claim per key pair.

This is the smallest policy change that fits the current signer-anchored write model. Each key can establish one username once, without reopening composite-profile write authority right now. The tradeoff remains that merged profiles still need a deterministic winner rule across single-claim member identities, but that is narrower than introducing resolved-profile-level write permissions in the same slice.
