## Problem
The application currently reads canonical post data directly from `records/posts` on demand and sorts threads from in-memory parsed records, which leaves no durable derived index for faster queries, normalized lookups, or commit-derived creation and update timestamps. The next slice should add a normalized SQLite index/cache that stays current on successful repo writes, can repair itself idempotently from canonical records plus git history, and can serve as the read model for sort-sensitive page flows without replacing the repository as the source of truth.

## User Stories
- As a developer, I want a SQLite-based normalized post index/cache so that read paths can use a structured derived model instead of reparsing canonical text files every time.
- As a developer, I want the SQLite index to update on successful repo writes so that page sorting and similar reads can rely on fresh derived data during normal operation.
- As a developer, I want schema creation and schema changes to run automatically and idempotently so that the index can be created or upgraded without manual migration steps.
- As a developer, I want post creation time and last update time derived from git commit timestamps so that read surfaces can sort by real repository history instead of by ad hoc `post_id` ordering.
- As a maintainer, I want the SQLite index to remain rebuildable from canonical records and git history so that manual repo edits, pulls, or history changes can be reconciled without treating SQLite as canonical data.

## Core Requirements
- The slice must add one normalized SQLite-derived read model for canonical post data and related queryable metadata, while keeping repository records and git history as the source of truth.
- The slice must update the SQLite index after successful repo writes and must also support idempotent rebuild or resync when the index is missing, stale, or drifted.
- The slice must manage schema creation and schema evolution automatically and idempotently without requiring a manual migration workflow.
- The slice must expose post creation time and post update time derived from git commit timestamps, not from transient runtime events or only the latest write path.
- The slice must be usable by existing read surfaces that need stable sort order or structured post lookup, while avoiding a broader rewrite of unrelated page behavior.

## Shared Component Inventory
- Existing canonical repository record model: reuse `records/posts` plus git history as the authoritative source; SQLite extends this as derived state and must not become an alternate write contract.
- Existing post parser/read model: extend the current `forum_web/repository.py` parsing and normalization rules as the canonical source for post-shape interpretation, rather than defining a separate SQLite-only parser.
- Existing repo write path: extend `forum_cgi/posting.py` and the other successful repo mutation flows that already end in `commit_post(...)` so SQLite refresh happens immediately after canonical writes succeed.
- Existing read consumers of sortable thread data: extend the board index and API index paths in `forum_web/web.py`, which currently depend on in-memory parsed post/thread order and are the clearest early consumers of commit-derived sort data.
- Existing direct file-read fallback: preserve the ability to derive state from canonical files and git history when SQLite is absent, stale, or being rebuilt, because repairability is part of the feature requirement.
- New SQLite index surface: add one focused derived-index layer because there is no current structured cache, migration surface, or commit-timestamp-backed post index in the repo.

## Simple User Flow
1. A canonical repo write succeeds through an existing application mutation path.
2. The application updates the SQLite-derived index so the new repository state is reflected in normalized queryable rows.
3. A read surface such as the home page or API index requests sortable thread data.
4. The read path uses the SQLite-derived model, including commit-derived creation and update times, to return consistently ordered data.
5. If the SQLite file is missing or drifted because repository state changed outside the normal app write flow, the application can rebuild or resync it from canonical records plus git history and continue serving the same derived contract.

## Success Criteria
- The repo contains one normalized SQLite-derived index/cache for post data that can be created automatically without manual setup.
- Successful canonical repo writes update the SQLite index so normal reads can rely on fresh derived sort and lookup data.
- Schema creation and schema changes run automatically and idempotently when the SQLite layer is opened or refreshed.
- The derived data includes post creation time and last update time based on git commit timestamps.
- At least one existing sort-sensitive read surface can use the SQLite-derived model instead of raw `post_id` ordering.
- The SQLite file can be rebuilt or resynced from canonical records and git history after external repo changes without changing the canonical repository contract.
