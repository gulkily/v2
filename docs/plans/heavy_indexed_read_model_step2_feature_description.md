# Heavy Indexed Read Model Step 2: Feature Description

## Problem
Hot public read routes still do too much request-time reconstruction from canonical text records, which keeps page latency higher than it should be. The next slice should move the hottest public reads onto a heavier indexed read model built on the existing post index while keeping canonical records authoritative.

## User Stories
- As a reader, I want `/`, `/threads/<id>`, and key public profile reads to load quickly so that the site feels responsive during ordinary browsing.
- As an operator, I want hot public routes to stop dominating slow-operation records so that real regressions and unusually heavy pages are easier to identify.
- As a maintainer, I want one primary indexed read model instead of multiple overlapping derived stores so that read performance improves without growing system sprawl.
- As a maintainer, I want canonical text records to remain the source of truth so that write behavior and repository integrity stay unchanged.

## Core Requirements
- The feature must shift an explicit allowlist of hot public read routes to indexed readback instead of reparsing and re-deriving full forum state on each request.
- Canonical text records must remain the authority for writes and for rebuilding the derived index.
- The indexed read path must preserve current public behavior for visibility, moderation effects, title resolution, and profile/account-related public read semantics.
- The feature must deepen the existing `post_index` path rather than introducing a second large read database.
- Non-hot or request-sensitive routes may stay on the current dynamic path until later slices.

## Shared Component Inventory
- `forum_core/post_index.py`: extend as the canonical derived read model because this repo already treats it as the primary SQLite index.
- `forum_web/web.py` public read handlers for board, thread, post, and profile pages: extend these canonical route surfaces to consume indexed read data rather than creating alternate endpoints.
- `forum_web/profiles.py` and current indexed profile/username helpers: reuse and expand the existing indexed profile-related read surfaces rather than forking profile logic into a second system.
- `forum_core/php_native_reads.py`, PHP-native snapshots, and PHP host cache/static-html layers: reuse as downstream consumers of the indexed read model rather than making them a separate source of truth.
- Existing slow-operation and timing surfaces: reuse as the canonical verification surface for whether the new indexed read path materially improves hot reads.

## Simple User Flow
1. A reader opens a hot public route such as `/` or `/threads/<id>`.
2. The request reads the needed page data from the indexed read model instead of reconstructing full repository state from raw records.
3. The page renders with the same visible behavior as before for titles, moderation, and public identity/read semantics.
4. After new content or moderation records are written, the existing derived-index refresh path updates the indexed model for later reads.

## Success Criteria
- Hot public routes no longer require full request-time repository reconstruction in their normal path.
- Production or local operator verification shows materially lower latency on the covered routes.
- Covered routes preserve current public behavior for moderation, title resolution, and public profile/thread visibility.
- The implementation deepens one existing indexed read model instead of adding a second large derived store.
- Slow-operation records become less dominated by ordinary board and thread reads.
