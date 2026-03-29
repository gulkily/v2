## Problem Statement
Choose the smallest safe way to let thread titles change for both thread owners and operators without breaking the append-only record model or creating ambiguous authority rules.

### Option A: Rewrite the root post subject
- Pros:
  - Simplest mental model for reads because the title still lives only on the root post.
  - Avoids adding a second title-resolution path.
- Cons:
  - Breaks the current append-only record pattern and weakens auditability.
  - Conflicts with signed-post immutability expectations.
  - Makes ownership and operator edits harder to reason about in git history.

### Option B: Add append-only signed thread-title update records
- Pros:
  - Matches the existing `profile-update` pattern for mutable metadata over immutable source records.
  - Preserves audit history for both user and operator title changes.
  - Lets reads resolve a current title without mutating canonical thread content.
- Cons:
  - Adds a new record type plus title-resolution logic in web and indexing paths.
  - Needs explicit policy for which identities may rename a thread and how operator actions are represented.

### Option C: Add operator-only title overrides outside the thread record model
- Pros:
  - Fastest path if the real need is curation rather than author editing.
  - Keeps user posting flows unchanged.
- Cons:
  - Does not satisfy the user story as written because regular users still cannot rename their own threads.
  - Splits title authority between original content and a separate operator overlay.
  - Likely needs a second mechanism later for user-initiated renames.

## Recommendation
Recommend Option B: append-only signed thread-title update records.

It fits the repository’s current direction for mutable metadata, keeps the original thread record immutable, and can cover both self-service user renames and operator actions within one auditable model. The main follow-up question for Step 2 is the authority policy: whether operators use the same record type with stronger validation or a distinct operator action path.
