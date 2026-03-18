## Problem Statement
Choose the smallest useful way to reduce operator-visible public-key file growth for signed posts, without weakening signature verification, breaking identity/bootstrap semantics, or turning the next loop into a full storage-model rewrite.

### Option A: Keep storing one public-key sidecar per signed post
- Pros:
  - Simplest current behavior to reason about.
  - Every signed post remains fully self-contained in repository storage.
  - Avoids any new reference or lookup rules.
- Cons:
  - Does not solve the operator problem of repeated public-key files.
  - Keeps repository growth tied to post count even when one key is reused many times.
  - Duplicates material already present in bootstrap and identity-link records.

### Option B: Reuse one previously stored canonical public-key copy for the same identity/key
- Pros:
  - Directly reduces file count for repeat signed posting.
  - Fits the existing model where identity bootstrap and later identity records already act as canonical key-bearing records.
  - Keeps the first-seen or newly introduced key explicit and inspectable while avoiding repeated storage on every post.
  - Smallest coherent change if the system treats signed posts as referencing an already visible key rather than republishing it.
- Cons:
  - Signed posts become less self-contained in raw storage because key material may live elsewhere.
  - Needs one deterministic rule for which existing stored copy counts as canonical.
  - Needs clear behavior when a signer introduces a new key for the first time or after rotation.

### Option C: Add a separate deduplicated key store keyed by fingerprint or content hash
- Pros:
  - Gives the cleanest long-term deduplication story.
  - Could support reuse across posts, profile updates, moderation actions, and merge records uniformly.
  - Separates key storage concerns from post and identity record families.
- Cons:
  - Larger scope than the operator need requires right now.
  - Introduces a new storage model alongside existing bootstrap and identity-link records.
  - Risks reopening broader questions about canonical ownership, migration, and historical compatibility.

## Recommendation
Recommend Option C: add a separate deduplicated key store keyed by fingerprint or content hash.

This is the better fit if the project wants one durable answer to repeated key storage instead of a posting-only shortcut. The loop should stay strict about boundaries:

- Keep signature verification requirements intact for signed submissions.
- Introduce one canonical storage location for public keys that can be reused across signed posts and other signed record families.
- Derive a deterministic lookup key for stored public keys so repeated submissions reuse the same stored artifact.
- Let signed records reference that canonical key material instead of writing a new per-record `.pub.asc` file.
- Leave historical backfill, aggressive repository compaction, and broader identity-model changes for later work.

That gives operators an explicit deduplication model rather than an implicit reuse rule hidden inside posting. The tradeoff is a somewhat larger next slice, but it creates a cleaner long-term storage contract.
