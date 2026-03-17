## Stage 1
- Goal: add the SQLite-derived index layer with automatic idempotent schema setup.
- Dependencies: approved Step 2; current canonical post parser in `forum_web/repository.py`; existing runtime repo-root/config patterns.
- Expected changes: add one focused SQLite index module that owns opening the database, applying schema creation or schema-version upgrades idempotently, and exposing normalized read/write entrypoints for derived post data; planned contracts such as `open_post_index(repo_root) -> PostIndex`, `ensure_post_index_schema(conn) -> None`, and `current_post_index_schema_version(conn) -> int`; conceptual database additions include normalized post/entity tables plus schema-version tracking, but no canonical data writes move into SQLite.
- Verification approach: create a fresh repo-local index, reopen it multiple times, and confirm schema setup or upgrade runs repeatably without duplicate rows or errors.
- Risks or open questions:
  - choosing a schema-version mechanism simple enough to stay idempotent
  - keeping the SQLite layer clearly derived rather than turning it into a second parser or source of truth
- Canonical components/API contracts touched: `forum_web/repository.py` parsing contract; repo-root/runtime configuration; new SQLite derived-index module.

## Stage 2
- Goal: populate normalized rows from canonical records and derive post creation/update times from git history, with rebuild or resync support.
- Dependencies: Stage 1; `records/posts`; current git metadata helpers in `forum_web/web.py`.
- Expected changes: add one index-build path that reads canonical post files through the existing parser, derives creation and last-update timestamps from relevant git commit history, and upserts normalized SQLite rows; add a rebuild or resync entrypoint for missing or drifted databases; planned contracts such as `rebuild_post_index(repo_root, index) -> IndexBuildResult`, `post_commit_timestamps(repo_root) -> dict[str, CommitTimestamps]`, and `upsert_indexed_post(index, parsed_post, timestamps) -> None`.
- Verification approach: build the index for a disposable repo with known commit history and confirm the derived creation/update timestamps match the expected earliest/latest commits for representative posts.
- Risks or open questions:
  - choosing a git-history scan shape that stays correct without becoming too expensive
  - defining how rebuild or resync detects and repairs drift after external repo changes
- Canonical components/API contracts touched: canonical post file format; git-history read contract; derived timestamp model in SQLite.

## Stage 3
- Goal: keep the SQLite index current during normal application writes.
- Dependencies: Stage 2; existing successful repo mutation flows that end in `commit_post(...)`, including thread creation, reply creation, task-status updates, moderation, identity linking, and profile updates.
- Expected changes: extend the canonical repo write paths so a successful commit triggers focused SQLite refresh for the affected records, while leaving canonical repo storage first in the sequence; planned contracts such as `refresh_post_index_after_commit(repo_root, *, commit_id: str, touched_paths: tuple[str, ...]) -> None` and `index_refresh_targets_from_paths(paths) -> tuple[str, ...]`; no new canonical write API or alternate persistence path.
- Verification approach: perform representative writes in a disposable repo, then confirm the SQLite index reflects the new or changed records and updated commit-derived timestamps without requiring a manual rebuild.
- Risks or open questions:
  - deciding how broad the touched-record refresh must be for non-post writes that affect derived metadata
  - ensuring SQLite refresh failures do not silently corrupt the canonical write contract
- Canonical components/API contracts touched: `forum_cgi/posting.py:store_post` and `commit_post(...)`; other repo mutation flows that reuse commit-backed writes; derived index refresh contract.

## Stage 4
- Goal: switch one sort-sensitive read surface to the SQLite-derived model and lock behavior into focused coverage.
- Dependencies: Stages 1-3; current board-index and API-index read paths in `forum_web/web.py`.
- Expected changes: route at least one existing sort-sensitive read path, likely the homepage thread ordering and corresponding API index path, through the SQLite-derived read model so ordering can use commit-derived creation/update timestamps instead of raw `post_id` ordering; add focused tests around schema idempotence, timestamp derivation, write-through refresh, rebuild or resync, and the selected read-surface ordering contract; planned contracts such as `load_visible_threads_from_index(...) -> list[IndexedThread]` or equivalent read helpers.
- Verification approach: manually create or update posts, load the selected read surface, and confirm ordering follows the derived timestamps; run targeted unittest coverage for index build, write-through refresh, and read ordering.
- Risks or open questions:
  - keeping the first read-surface migration narrow enough to avoid a broader read-model rewrite
  - choosing test fixtures that prove timestamp ordering without depending on fragile wall-clock assumptions
- Canonical components/API contracts touched: board index route; API list-index route; focused read-order and SQLite-index tests.
