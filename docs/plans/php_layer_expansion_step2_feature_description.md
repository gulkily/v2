# Step 2 – Feature Description: PHP Native Thread Detail Pages

## Problem

Thread detail pages (`/threads/{id}`) are the second-most accessed route after the board index, but every cache miss still incurs per-request Python CGI execution (50–500ms overhead). The established PHP-native pattern (shared contract → prepared snapshot → PHP renderer) has already succeeded for the board index; extending it to threads will capture the next tier of performance gains without creating a new architecture.

## User Stories

- As an operator on a PHP-hosted deployment, I want thread detail pages to avoid per-request Python execution on cache misses so that traffic spikes don't overload the Python backend.
- As an anonymous reader, I want thread pages to load quickly even when the microcache is cold or static HTML is missing.
- As a maintainer, I want the thread read contract to reuse the proven board-index pattern (contract → snapshot → renderer) so future routes follow a predictable template.
- As a maintainer, I want Python to remain authoritative for thread data preparation, visibility rules, and cache invalidation so PHP stays a read-only rendering layer.

## Core Requirements

- The PHP native thread renderer must serve only bare `/threads/{id}` requests with no query parameters, no cookies, and no authentication headers (same eligibility rules as board index).
- Thread snapshots must include all data needed to render the thread discussion tree: root post metadata, reply structure, author/signature display, moderation state, and related metadata (thread tags, reply counts, etc.).
- Thread snapshots for this route must be stored in the shared SQLite snapshot database at `state/cache/php_native_reads.sqlite3`; this phase does not introduce new JSON snapshot files.
- Python must eagerly refresh affected thread snapshots after every write that changes thread rendering, including post commits, moderation changes, thread title updates, and identity/profile changes that affect author display.
- RSS feeds (`?format=rss`), expanded views, and other query-parameterized reads remain Python-only (not duplicated in PHP).
- Non-anonymous requests and authenticated user context must bypass the PHP native path (continue using Python). Signed content inside an otherwise public thread remains renderable in the native path.
- The thread renderer must fall back gracefully: if the snapshot is missing, unreadable, or the request is ineligible, the PHP host prefers existing static HTML first and then falls through to the Python CGI path.
- Read-time fallback must not rebuild or repair SQLite snapshots inline; refresh remains a write-time concern, with separate operator tooling for rebuild/backfill.
- The host must emit operator-visible signals for thread native hits and fallbacks so deployments can measure how often the safety-net path is being used.

## Shared Component Inventory

- Existing PHP host entry layer in `php_host/public/index.php` and `php_host/public/cache.php`: extend to add thread route eligibility check and native renderer.
- Existing Python thread render logic in `forum_web/web.py` (`render_thread_detail_page()`): keep as the authoritative definition of thread page structure, visibility rules, and content formatting.
- Existing post index in `forum_core/post_index.py` and repository loading infrastructure: extend to support thread snapshot generation alongside board snapshot.
- Existing post commit hook in `forum_cgi/posting.py` (`commit_post()`): reuse the same refresh hook to invalidate and rebuild thread snapshots.
- Existing PHP snapshot infrastructure from board index work in `forum_core/php_native_reads.py`: extend with `build_thread_snapshot(thread_id)` builder.
- Current state: the existing board-index native-read artifact is still written as JSON at `state/cache/php_native_reads/board_index_root.json`.
- New thread-route requirement: use dedicated SQLite storage at `state/cache/php_native_reads.sqlite3` for thread snapshots in this phase; do not introduce per-thread JSON files. See `php_layer_snapshot_storage_design.md` for detailed schema and rationale.

## Simple User Flow

1. An anonymous visitor requests `/threads/{thread-id}` with no query parameters, cookies, or auth headers.
2. The PHP host checks for a static HTML thread page first; if it exists, that response is served and the native PHP path is skipped.
3. If static HTML is unavailable, the PHP host checks if the request is eligible for native rendering (bare GET, no credentials, thread route allowlisted).
4. If eligible, PHP queries the SQLite snapshot database (`state/cache/php_native_reads.sqlite3`) for the thread snapshot.
5. PHP renders the full thread discussion tree, post metadata, signatures, and reply structure directly from the snapshot without invoking Python.
6. If the snapshot is missing, unreadable, or the request is ineligible, PHP falls through to the existing Python CGI path without attempting inline snapshot repair.
7. When an authoritative write changes thread rendering, Python refreshes the affected thread snapshots in the SQLite database so eligible future reads usually hit current data.

## Success Criteria

- Thread detail pages can be served via native PHP rendering without per-request Python CGI execution on cache misses.
- Thread snapshots are deterministic and synchronized with repository state (same snapshot generated by Python for consistent reads).
- Writes that affect thread rendering (new posts, moderation actions, thread title updates, identity/profile display changes) transparently invalidate and rebuild affected thread snapshots.
- Query-parameterized requests (`?format=rss`, `?view=expanded`, etc.) continue to use the Python path without regression.
- Authenticated requests and non-bare reads continue to use the Python path (no personalized behavior leaked to cached PHP renders).
- Thread rendering latency improves from ~100–300ms (Python) to ~20–50ms (native PHP) for eligible requests.
- Test coverage demonstrates parity between PHP native and Python thread renders for representative thread structures (nested replies, signatures, moderation state).
- Operators can observe native-hit versus fallback behavior for thread routes and detect when missing/stale snapshot fallback happens more than expected.
