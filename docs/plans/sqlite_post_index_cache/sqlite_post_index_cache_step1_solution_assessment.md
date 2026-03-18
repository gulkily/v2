## Problem Statement
Choose the smallest coherent way to add a SQLite-based derived post index/cache with normalized data, automatic idempotent schema evolution, and stored post creation/update times derived from git commit timestamps without making SQLite the new source of truth.

### Option A: Build a normalized SQLite read model as a derived index that updates on successful repo writes and can rebuild from canonical records plus git history
- Pros:
  - Best fit for the request because normalization, schema upgrades, commit-derived timestamps, and read-time sort support can all be handled in one explicit index path.
  - Keeps the repository text records and git history canonical while SQLite stays derived state instead of becoming the source of truth.
  - Supports normal page reads efficiently because the index can stay current immediately after successful repo writes.
  - Makes idempotent schema changes straightforward through a dedicated schema-version/migration layer.
  - Gives one consistent place to compute both creation time and latest update time from commit history for each post, while still allowing rebuild/resync if repo state changed outside the app.
- Cons:
  - Requires both a write-through update path and a rebuild/resync path.
  - Needs clear rules for detecting and repairing drift when repository changes happen outside the normal app write flow.

### Option B: Add an incremental SQLite cache updated mainly during writes, with partial backfill for older records
- Pros:
  - Can reduce initial indexing cost by doing less work up front.
  - Fits flows where most new data arrives through the app's own write paths.
- Cons:
  - Weaker fit for the request because commit-derived creation/update times for existing records become harder to guarantee consistently.
  - Risks drift when records change outside the current write path or when older history must be backfilled later.
  - Makes normalization and schema evolution harder to reason about because the cache can exist in partially populated states.

### Option C: Store a flatter denormalized SQLite cache with minimal migration logic
- Pros:
  - Smallest short-term implementation surface.
  - Easier to query initially for a few read cases.
- Cons:
  - Conflicts with the request for data normalization.
  - Makes future schema changes and cross-entity queries more awkward as post metadata grows.
  - Pushes creation/update timestamp handling toward ad hoc columns and duplicated derivation rules instead of one coherent model.

## Recommendation
Recommend Option A: build a normalized SQLite read model as a derived index that updates on successful repo writes and can rebuild from canonical records plus git history.

This is the smallest option that satisfies all four requirements together while also supporting page sorting from SQLite in normal operation. The repo remains canonical, SQLite stays derived, successful repo writes immediately refresh the index for fast reads, and a rebuild/resync path preserves correctness when records or git history change outside the application's write flow.
