## Problem
The current derived SQLite post index stores post-shaped metadata such as signer fingerprint on the `posts` row, but it does not provide a normalized author model that can include author-facing data such as names and fingerprints in one coherent indexed structure. The next slice should extend the derived SQLite index with normalized author data so read paths can access author names and fingerprints through SQLite without weakening the repo-as-canonical contract or the current idempotent schema-evolution model.

## User Stories
- As an operator, I want author data such as names and fingerprints included in the SQLite index so that read paths can query it without reparsing canonical records on demand.
- As a developer, I want that author data stored in a normalized structure so that identity-shaped information is not duplicated across every indexed post row.
- As a developer, I want schema changes for the new author data to apply automatically and idempotently so that the derived index continues to open and upgrade without manual migration work.
- As a maintainer, I want the author data in SQLite to remain derived from canonical records and existing identity-resolution logic so that the repository stays the source of truth.
- As a future UI developer, I want author names and fingerprints available through the derived index so that listing and detail views can use them without adding another read-side lookup path.

## Core Requirements
- The slice must extend the derived SQLite index so it includes author-related data such as names and fingerprints.
- The slice must keep author data normalized rather than duplicating all author fields directly onto every indexed post row.
- The slice must preserve the repo and existing canonical parsing or identity-resolution logic as the source of truth for author data.
- The slice must manage schema creation and schema evolution for the new author data automatically and idempotently.
- The slice must support rebuild or resync from canonical records so author data can be repaired after external repo changes.
- The slice must remain compatible with the current post-index refresh model that runs after successful repo writes.

## Shared Component Inventory
- Existing SQLite derived index: extend `forum_core/post_index.py` rather than creating a second cache or side database for author data.
- Existing indexed post model: adapt the current `posts` table and related normalized child tables so author entities can be linked cleanly from indexed posts.
- Existing canonical post parser: reuse the current post parsing contract in `forum_web/repository.py`, including signer and identity-related fields already exposed there.
- Existing identity-resolution or profile logic: reuse the current resolved author-name surface where possible rather than inventing a separate SQLite-only notion of author names.
- Existing schema-version and idempotent upgrade behavior: preserve `ensure_post_index_schema(...)` as the place where the new normalized author schema is created or upgraded.
- Existing rebuild and refresh paths: extend the current index build and post-write refresh flow so author rows stay derived and current alongside indexed posts.

## Simple User Flow
1. A canonical post record is parsed through the existing repository and identity-resolution logic.
2. The SQLite index build or refresh path stores the post row and the normalized author data linked to that post.
3. A read surface requests indexed post data and can obtain author names and fingerprints from the derived SQLite model.
4. If the index is rebuilt or resynced from canonical records, the author data is rederived and restored automatically without any manual repair steps.

## Success Criteria
- The SQLite index includes author data such as names and fingerprints.
- The author data is stored in a normalized structure linked from indexed posts.
- Schema setup or upgrades for the author data run automatically and idempotently.
- Rebuild or resync from canonical records restores the author data correctly.
- The feature keeps SQLite derived and does not introduce a second source of truth for author identity information.
