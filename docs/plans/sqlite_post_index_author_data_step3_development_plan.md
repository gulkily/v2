## Stage 1
- Goal: extend the SQLite-derived schema and indexed row model with normalized author entities.
- Dependencies: approved Step 2; existing `forum_core/post_index.py` schema layer; current indexed `posts` table and related normalized child tables.
- Expected changes: add normalized author-oriented tables or link structures so indexed posts can reference author rows that carry names and fingerprints, while preserving idempotent schema setup and upgrade behavior; planned contracts such as expanded `ensure_post_index_schema(...)`, new author-row upsert helpers, and any small indexed-row model updates needed to expose author links cleanly; no canonical data writes move into SQLite.
- Verification approach: open a fresh index, reopen an existing index, and confirm the new author schema is created or upgraded idempotently without duplicate rows or migration errors.
- Risks or open questions:
  - choosing the minimal normalized author shape that can hold names and fingerprints without overfitting future identity needs
  - keeping the schema change compatible with existing indexed post rows and upgrade paths
- Canonical components/API contracts touched: `forum_core/post_index.py`; SQLite schema versioning or upgrade behavior; indexed post-to-author relationship model.

## Stage 2
- Goal: populate and refresh normalized author data from canonical records and current identity-resolution logic.
- Dependencies: Stage 1; existing post-index rebuild path; current post parser and resolved identity or profile logic.
- Expected changes: extend index rebuild and targeted refresh so author rows and post-to-author links are derived alongside indexed posts, using canonical signer or identity fields plus the current resolved author-name surface where available; planned contracts such as author upsert helpers during `rebuild_post_index(...)` and refresh paths that keep author rows current after successful repo writes.
- Verification approach: build or refresh the index in a disposable repo with representative posts and author metadata, then confirm the author names and fingerprints appear in the expected normalized rows and remain correct after rebuild.
- Risks or open questions:
  - deciding which author name source is canonical enough to index when multiple identity-related surfaces exist
  - ensuring non-post writes that affect resolved author names are reflected correctly in targeted refreshes
- Canonical components/API contracts touched: post-index rebuild flow; post-write refresh flow; current identity-resolution or profile-derived author naming logic.

## Stage 3
- Goal: expose the author data through focused tests and one narrow read-side contract without broadening the feature into a new identity subsystem.
- Dependencies: Stages 1-2; current post-index tests; existing read helpers that consume indexed rows.
- Expected changes: add focused regression tests for normalized author-row creation, idempotent upgrades, rebuild or refresh correctness, and indexed access to author names and fingerprints; optionally extend one narrow read helper or indexed row projection so the author data is reachable in a stable way for future UI use; planned contracts such as expanded `IndexedPostRow` or a new indexed author projection helper, if needed.
- Verification approach: run targeted unittest coverage for schema upgrade, rebuild, refresh, and indexed author lookups; confirm the author data can be retrieved without falling back to reparsing canonical files.
- Risks or open questions:
  - keeping the first read-side exposure narrow enough to avoid a broader identity-model rewrite
  - choosing tests that prove normalization rather than only checking one duplicated field value
- Canonical components/API contracts touched: post-index tests; any indexed row or read-helper projection that surfaces author names and fingerprints.
