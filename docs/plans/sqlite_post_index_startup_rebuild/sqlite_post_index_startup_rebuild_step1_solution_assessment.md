## Problem Statement
Choose the smallest coherent way to ensure the derived SQLite post index fully backfills new schema-dependent data after upgrades, instead of exposing partially upgraded state such as empty new tables.

### Option A: Force a full rebuild whenever the SQLite schema version changes, and run the same readiness check at startup and on first indexed use
- Pros:
  - Best fit for the request because schema upgrades and data backfills stay coupled instead of allowing partially upgraded databases.
  - Matches the desired behavior directly: rebuild eagerly on server startup and also lazily on first indexed request if needed.
  - Keeps the readiness contract simple: an index is either current for this schema version or it is rebuilt before use.
  - Works well with the current derived-state model because rebuilds already rederive data from canonical records plus git history.
- Cons:
  - Startup can block longer on large repositories because rebuild is no longer deferred or time-limited.
  - Requires one clear guard against redundant duplicate rebuilds when startup and first-request checks both run.

### Option B: Add per-feature backfill markers and repair only missing new tables or rows after schema upgrades
- Pros:
  - Can reduce rebuild cost by targeting only the newly added data.
  - Leaves room for more selective future repair logic.
- Cons:
  - More complex than the current need because every new schema feature would need its own drift or backfill detection.
  - Easier to get wrong, especially when derived tables depend on shared identity or repository state.
  - Risks more partial-upgrade bugs like the one just observed.

### Option C: Keep schema upgrades lightweight and rely on future writes to gradually fill new derived tables
- Pros:
  - Smallest implementation surface.
  - Avoids startup rebuild cost.
- Cons:
  - Does not satisfy the request because old data remains missing until touched again.
  - Leaves the index in partially upgraded states that are hard to reason about operationally.
  - Produces incorrect reads for historical data after schema changes.

## Recommendation
Recommend Option A: force a full rebuild whenever the SQLite schema version changes, and run the same readiness check at startup and on first indexed use.

This is the smallest approach that actually fixes the observed behavior. It keeps the SQLite index derived and trustworthy: after a schema change, the app rebuilds the index completely rather than exposing a half-migrated database with missing backfilled rows.
