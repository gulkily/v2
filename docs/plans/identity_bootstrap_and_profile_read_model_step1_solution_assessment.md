## Problem Statement
Choose the smallest useful way to make identity bootstrap and profile lookup coherent after Loop 5, without turning the next loop into full key rotation, profile editing, moderation trust rules, or a second rewrite of posting.

### Option A: Add a dedicated identity record type and explicit registration flow now
- Pros:
  - Makes identity creation explicit instead of inferring it from ordinary posts.
  - Gives profiles a cleaner long-term home if identity records later grow to include key merges, profile updates, and trust metadata.
  - May reduce ambiguity between discussion content and identity bootstrap content.
- Cons:
  - Larger scope for the next loop.
  - Reopens record-model questions that the current architecture has intentionally deferred.
  - Delays the first demonstrable `get_profile` path because the system would need both new write semantics and new read semantics at once.

### Option B: Bootstrap identity from a public-key post and derive a read-only profile summary from visible records
- Pros:
  - Aligns with the existing architecture notes and protocol draft.
  - Builds directly on the signed posting path already implemented in Loop 5.
  - Keeps the next loop small: define one bootstrap post shape, derive a stable identity identifier, and add `get_profile` plus a user/profile view.
  - Preserves the project goal that git-tracked text remains the canonical source of truth.
- Cons:
  - Uses an ordinary post as the first identity anchor, which is less clean than a dedicated record model.
  - Requires careful rules so implementations agree on which post counts as the bootstrap record and how profile summaries are derived.
  - May need later migration or normalization once identity merge and profile-update records exist.

### Option C: Infer identity entirely from signed posts for now and defer explicit bootstrap
- Pros:
  - Smallest immediate implementation surface.
  - Avoids introducing any new record shape in the next loop.
  - Lets the system expose a minimal author view based only on signing fingerprints already present on posts.
- Cons:
  - Weakens the notion of intentional identity bootstrap.
  - Makes `get_profile` and user/profile pages less coherent because there is no explicit profile anchor.
  - Conflicts with the current architecture direction that a user establishes identity by posting a public key.

## Recommendation
Recommend Option B: bootstrap identity from a public-key post and derive a read-only profile summary from visible records.

This is the smallest coherent slice that turns the current signing work into an actual identity surface without dragging the loop into full profile management. The loop should stay strict about boundaries:

- Define one minimal public-key bootstrap post shape that is easy to create, inspect, and validate.
- Treat the bootstrap post as the first profile anchor and derive a stable `Identity-ID` from that visible identity material.
- Add deterministic `get_profile` output and a simple user/profile view based on repository data already present.
- Reuse the existing detached-signature model and browser key flow instead of inventing a second identity transport.
- Leave key rotation, multi-key merge records, moderator-trusted identity assertions, and profile editing for later loops.

That gives the project a visible identity model quickly: a user can establish identity by publishing their public key in the repo, and readers can retrieve a stable derived profile summary from canonical data. The tradeoff is that the first identity layer remains intentionally plain and text-native rather than fully normalized.
