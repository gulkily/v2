## Problem Statement
Choose the smallest coherent way to extend the derived SQLite post index so it includes author data such as names and fingerprints without weakening normalization or the current idempotent schema-evolution model.

### Option A: Add normalized author tables linked from indexed posts
- Pros:
  - Best fit for the request because names, fingerprints, and future author metadata can live in one normalized place instead of being duplicated on every indexed post row.
  - Builds naturally on the current normalized SQLite read model and keeps schema growth coherent as author data expands.
  - Works well with idempotent schema evolution because new tables and foreign-key columns can be added without rewriting the canonical repo model.
  - Makes later author-oriented reads or filters easier if the UI needs them.
- Cons:
  - Slightly broader implementation than adding one more column to `posts`.
  - Requires deciding how to map current post fields such as signer fingerprint and resolved display name into one author entity shape.

### Option B: Add author-name fields directly onto the existing `posts` table
- Pros:
  - Smallest short-term implementation surface.
  - Easy to wire into existing post upserts because the current index already stores some post-local author-related fields.
- Cons:
  - Weaker fit for the normalization requirement because author names and fingerprints would be duplicated across many post rows.
  - Makes future schema growth around identities or author metadata harder to reason about.
  - Encourages post-shaped storage for data that is conceptually author-shaped.

### Option C: Keep the current post index minimal and derive author data only at read time from canonical records
- Pros:
  - Avoids expanding the SQLite schema immediately.
  - Keeps author display logic closer to existing web rendering code.
- Cons:
  - Does not satisfy the request as directly because the author data would not actually be included in the SQLite index.
  - Weakens the value of SQLite as the normalized read model for sort- and listing-sensitive surfaces.
  - Reintroduces repeated parsing or lookup work on reads.

## Recommendation
Recommend Option A: add normalized author tables linked from indexed posts.

This is the smallest approach that satisfies the request while staying aligned with the existing SQLite feature direction. The repo remains canonical, SQLite remains derived, schema changes stay idempotent, and author data such as names and fingerprints gains one coherent normalized home instead of being spread redundantly across post rows.
