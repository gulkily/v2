## Problem Statement
Choose the smallest useful way to introduce moderation as a first-class, signed, auditable part of repository state without collapsing the next loop into deletion policy, bans, or a second parallel state model.

### Option A: Add signed moderation records as canonical text files and derive visible state from them
- Pros:
  - Aligns directly with the git-backed and auditable architecture already described in the repo docs.
  - Keeps moderation actions inspectable as plain ASCII records instead of hidden mutable flags.
  - Reuses the existing signing and identity work rather than inventing a separate trust mechanism.
  - Gives one coherent loop outcome: signed moderation write path, moderation log, and read-time effects for `hide`, `lock`, `pin`, and `unpin`.
- Cons:
  - Requires careful visible-state rules so reads stay deterministic when multiple moderation records target the same post or thread.
  - Adds another canonical record family and another place where future multi-language implementations must match behavior exactly.
  - Needs a first-cut moderator authorization rule even if that rule stays simple.

### Option B: Store moderation state in local mutable flags or config first, and add signed records later
- Pros:
  - Smaller immediate implementation surface.
  - Faster path to changing what the local instance shows.
  - Avoids defining a moderation record shape right away.
- Cons:
  - Conflicts with the stated requirement that moderation actions be signed and stored in git.
  - Produces a side-state model that is harder to mirror across implementations and clones.
  - Delays the auditable moderation log, which is one of the main reasons to introduce moderation this way.

### Option C: Represent moderation by editing post files or deleting content directly in the next loop
- Pros:
  - Very small apparent implementation surface for simple hide/remove behavior.
  - Changes are immediately visible without deriving moderation state from separate records.
- Cons:
  - Mixes moderation state into content state and makes later hard-purge work more confusing.
  - Does not map cleanly to `lock`, `pin`, and `unpin`, which are actions on visibility and interaction rather than content mutation.
  - Undercuts the auditability and decentralization goals, because moderation intent becomes harder to inspect as a distinct artifact.

## Recommendation
Recommend Option A: add signed moderation records as canonical text files and derive visible state from them.

This is the smallest coherent slice that keeps moderation compatible with the rest of the architecture. The loop should stay strict about boundaries:

- Define one minimal moderation record shape stored separately from post content.
- Treat `hide`, `lock`, `pin`, and `unpin` as signed moderation actions with explicit targets.
- Add a deterministic moderation log read surface and make the existing thread/index reads honor visible moderation state.
- Keep moderator authorization simple for this loop, such as an instance-local allowlist of trusted moderator fingerprints.
- Leave bans, scheduled deletion, tombstones, and hard-purge behavior for later loops.

That gives the project a real moderation model without smuggling policy into mutable server state. A moderator can sign an action, the action is committed to git, the public instance changes what it shows, and readers can inspect the moderation log as part of repository-backed state.
