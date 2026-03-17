## Stage 1 - Add normalized author schema and helper model
- Changes:
  - Extended `forum_core/post_index.py` with an `authors` table, a post-to-author link column, and an idempotent schema upgrade path for the normalized author model.
  - Added helper dataclasses and author-derivation helpers so names and fingerprints can be represented as author-shaped indexed rows instead of only post-local columns.
  - Expanded `tests/test_post_index.py` with schema-upgrade coverage for the author tables and focused helper tests for canonical-identity and fingerprint-fallback author derivation.
- Verification:
  - Ran `python -m unittest tests.test_post_index`
- Notes:
  - This stage adds the schema and helper model only. Rebuild and refresh paths still begin populating the normalized author rows in Stage 2.

## Stage 2 - Populate author rows during rebuild and refresh
- Changes:
  - Updated `forum_core/post_index.py` so `rebuild_post_index(...)` now derives normalized author rows using the existing identity-resolution flow and stores post-to-author links alongside indexed posts.
  - Extended the incremental refresh path so post-index refreshes keep author rows current after successful repo writes, and fall back to a full rebuild when profile or identity records change author-facing metadata.
  - Expanded `tests/test_post_index.py` with rebuild coverage that asserts normalized author rows and post-to-author links are actually populated.
- Verification:
  - Ran `python -m unittest tests.test_post_index`
- Notes:
  - This stage keeps author data derived from canonical records and existing identity-resolution logic rather than introducing a new identity source.
