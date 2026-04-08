# Heavy Indexed Read Model Step 1: Solution Assessment

Problem statement: Public read requests are still reconstructing too much forum state from canonical text records at request time, so we need a heavier indexed read path that materially reduces board/thread/profile latency without breaking canonical-record correctness.

## Option A — Expand the existing SQLite post index into the primary read model for hot public reads
- Pros
- Reuses the current `post_index.sqlite3` investment instead of introducing a second major read store.
- Keeps canonical text records as the source of truth while shifting board/thread/profile reads to indexed queries.
- Fits the current Python app, PHP-native snapshots, and startup/readiness flow with less system sprawl.
- Cons
- Requires substantial read-path refactoring because many handlers currently expect fully materialized `Post` lists and derived state.
- Raises index completeness pressure: moderation, title updates, profile/merge state, and task metadata need reliable indexed projections.

## Option B — Add a separate read-optimized SQLite model alongside the current post index
- Pros
- Allows a clean schema designed specifically for public read pages instead of stretching the current post index contract.
- Can keep the existing post index focused on helper/look-up use cases while the new store serves page reads.
- Cons
- Creates two large derived SQLite systems with overlapping source data and invalidation rules.
- Increases rebuild, debugging, and operator complexity.

## Option C — Lean primarily on generated HTML / PHP-native snapshots and widen snapshot coverage
- Pros
- Likely fastest anonymous reads because hot pages can be served with minimal application work.
- Builds on the existing PHP-native snapshots, static HTML, and microcache layers already in the repo.
- Cons
- Helps only the routes and request shapes covered by snapshots.
- Makes freshness, invalidation, and per-user/self-view behavior more complex.
- Risks growing a parallel rendering system instead of fixing the canonical read model.

Recommendation: Option A.

Why: It is the smallest architectural shift that can deliver Pollyanna-style heavier indexing in this codebase. The repo already has one canonical derived SQLite store, one readiness/rebuild path, and multiple consumers of indexed data. The next steps should deepen that single indexed read model for the hottest public pages instead of adding a second large store or relying primarily on snapshot sprawl.
