## Stage 1 - Add normalized author schema and helper model
- Changes:
  - Extended `forum_core/post_index.py` with an `authors` table, a post-to-author link column, and an idempotent schema upgrade path for the normalized author model.
  - Added helper dataclasses and author-derivation helpers so names and fingerprints can be represented as author-shaped indexed rows instead of only post-local columns.
  - Expanded `tests/test_post_index.py` with schema-upgrade coverage for the author tables and focused helper tests for canonical-identity and fingerprint-fallback author derivation.
- Verification:
  - Ran `python -m unittest tests.test_post_index`
- Notes:
  - This stage adds the schema and helper model only. Rebuild and refresh paths still begin populating the normalized author rows in Stage 2.
