# Step 3 – Development Plan: PHP Native Thread Detail Pages

## Overview

This plan breaks the thread expansion into six atomic stages with explicit dependencies, verification points, and clear boundaries. The goal is to extend the proven PHP-native pattern to `/threads/{id}` using SQLite-backed snapshots for the thread route while keeping static HTML as the preferred read path when available.

---

## Stage 1: Thread Read Contract

**Goal**: Define the explicit shared contract for bare `/threads/{id}` requests that PHP can handle natively.

**Dependencies**: 
- Approved Step 2 (feature description)
- Existing `forum_web/web.py` (`render_thread_detail_page()`) to understand current thread rendering
- Board index contract from `php_host_native_read_performance_shared_read_contract.md` (as template)

**Expected changes**:
- New document: `docs/plans/php_layer_thread_shared_read_contract.md` defining:
  - Request eligibility (bare `/threads/{id}`, no query params, no auth, no cookies)
  - Visibility and moderation rules (which threads/posts are visible, which are hidden)
  - Snapshot data structure: full reply tree, post metadata, signatures, author display, moderation markers, and the additional page-shell/thread-meta fields needed for parity with the current Python thread page
  - Cache invalidation boundaries (which write paths must refresh affected thread snapshots)
  - Fallback semantics (static HTML preferred, then PHP native, then Python; no inline snapshot repair on read fallback)
  - Deterministic invalidation ownership matrix for each write path that can change `/threads/{id}` output

**Verification approach**:
- Manual code review: compare board index contract against thread rendering logic to ensure similar eligibility/visibility model
- Representative test cases: verify contract covers nested replies, signatures, moderation state, thread types (discussion vs. task)
- Confirm that the contract excludes: RSS feeds, query-parameterized reads, personalized views, authenticated users
- Confirm that the contract covers current thread-page affordances that remain in scope for parity: reply CTA, lock-state messaging, change-title affordance, feed link, and root-context blocks
- Confirm that every authoritative write path has one owning refresh rule and one deterministic way to resolve affected thread IDs

**Risks or open questions**:
- How deep should thread nesting be? (Reply to reply to reply — should all be included?)
- **Decision**: Include all nesting levels; no depth limit. (Can optimize rendering if needed later.)
- Should moderation state (hidden posts/threads) be reflected in the snapshot?
- **Decision**: Yes; Python builds snapshot with visibility rules applied (hidden posts omitted or marked).
- Should signed posts force thread fallback?
- **Decision**: No; signed content remains renderable in native PHP. Only authenticated or otherwise ineligible requests bypass the native path.

**Estimated effort**: 2–4 hours

**Canonical components touched**: Thread route eligibility, visibility rules, snapshot schema, cache invalidation policy

---

## Stage 2: Thread Snapshot Schema & Access

**Goal**: Add SQLite-backed snapshot storage for thread native reads and the shared access helpers needed by the PHP host, without bundling a board-index storage migration into this thread project.

**Dependencies**:
- Stage 1 (contract establishes what data goes in snapshots)
- Design doc: `php_layer_snapshot_storage_design.md`

**Expected changes**:
- New Python module: `forum_core/php_native_reads_db.py` with:
  - `ensure_php_native_snapshots_schema(connection)` – create tables and indexes
  - `save_php_native_snapshot(connection, snapshot_id, entity_type, entity_id, snapshot_json)` – insert/update snapshot
  - `load_php_native_snapshot(connection, snapshot_id)` – retrieve snapshot JSON
  - `list_snapshots_by_type(connection, entity_type)` – list all snapshots of a type (for debugging)
  - optional counters/metadata helpers needed for operator visibility into fallback frequency or stale/missing rows

- Update `forum_core/php_native_reads.py`:
  - Add thread snapshot write helpers that persist only to SQLite for this route
  - Do not introduce per-thread JSON snapshots
  - Do not require board-index JSON migration as part of this phase

- Update `forum_cgi/posting.py`:
  - Modify the shared post-commit refresh path so writes affecting thread rendering refresh thread snapshots in SQLite

- New operator task in `scripts/forum_tasks.py`:
  - Add a snapshot rebuild/backfill command for PHP native reads (for example `./forum rebuild-php-native-snapshots`)
  - Support rebuilding all thread snapshots and targeted rebuilds by thread ID
  - Keep this tooling separate from normal read fallback so repair remains operator-driven

- Schema: `php_native_snapshots` table with columns: `snapshot_id`, `entity_type`, `entity_id`, `snapshot_json`, `created_at`, `refreshed_at`, `invalidated_by_post_id`, `entity_version`

**Verification approach**:
- Unit tests: `test_php_native_reads_db.py` — verify save/load operations, schema creation, snapshot updates
- Integration tests: verify thread snapshot rows can be created, loaded, and refreshed from authoritative write paths
- Verify operator-visible metadata or counters can expose missing/fallback behavior without mutating the read path
- Verify the rebuild/backfill command can populate an empty snapshot database from canonical records

**Risks or open questions**:
- What if PHP runtime doesn't have SQLite3 extension enabled?
- **Decision**: Treat SQLite3 support as a prerequisite for the thread native-read feature. If unavailable, thread reads fall through to static HTML or Python; do not add a JSON escape hatch for this route.

**Estimated effort**: 6–10 hours

**Canonical components touched**: Snapshot storage, database schema, invalidation hooks, operator observability metadata

---

## Stage 3: Python Thread Snapshot Builder

**Goal**: Extend Python to generate and refresh thread snapshots in SQLite, following the contract from Stage 1.

**Dependencies**:
- Stage 1 (thread contract defines snapshot structure)
- Stage 2 (SQLite schema and API ready)
- Existing thread rendering logic in `forum_web/web.py` (`render_thread_detail_page()`)
- Post index infrastructure (`forum_core/post_index.py`)

**Expected changes**:
- New Python function in `forum_core/php_native_reads.py`:
  - `build_thread_snapshot(thread_id: str, repo_root: Path) -> dict[str, object]` – generate thread snapshot matching Stage 1 contract
    - Load thread root post
    - Load all replies (recursively, respecting nesting)
    - Apply moderation visibility rules
    - Include author metadata, signatures, tags
    - Return structured JSON-serializable dict

- Extend commit hook in `forum_cgi/posting.py`:
  - When a write affecting thread rendering is committed, determine which thread snapshots need refresh
  - Cover at least: new thread/reply posts, moderation actions affecting a thread or its replies, thread title updates, and identity/profile changes that alter rendered author display
  - Call snapshot builder for each affected thread
  - Write to SQLite via db module

- Deterministic invalidation ownership matrix:
  - Post create or reply commit: refresh the root thread for the committed post
  - Moderation record targeting a thread: refresh that target thread
  - Moderation record targeting a post: refresh the target post's root thread
  - Thread title update: refresh the updated thread
  - Profile/identity update that changes rendered author display: refresh each visible thread containing posts authored by the affected identity

- Add tests: `test_php_native_reads.py` extended with:
  - `test_build_thread_snapshot_structure()` – verify snapshot matches contract
  - `test_build_thread_snapshot_respects_moderation()` – hidden posts not in snapshot
  - `test_build_thread_snapshot_includes_nested_replies()` – replies to replies included
  - `test_commit_post_refreshes_thread_snapshot()` – post-write hook integration works
  - `test_moderation_thread_target_refreshes_thread_snapshot()` – thread moderation invalidation works
  - `test_moderation_post_target_refreshes_thread_snapshot()` – post moderation invalidation works
  - `test_thread_title_update_refreshes_thread_snapshot()` – title-change invalidation works
  - `test_profile_or_identity_change_refreshes_thread_snapshot()` – author-display invalidation works
  - `test_rebuild_php_native_snapshots_backfills_thread_rows()` – rebuild command backfills from canonical records

**Verification approach**:
- Run thread-specific unit tests
- Run existing test suite to ensure no regression in Python rendering
- Smoke test: manually verify snapshot JSON structure matches contract

**Risks or open questions**:
- How to handle very large threads (100s of replies)?
- **Decision**: Build full tree; optimize rendering if needed later. Verify performance is acceptable in smoke tests.
- What if a post is moderated after the snapshot is built?
- **Decision**: Moderation actions should also trigger snapshot refresh (handled in moderation API, not just post commit).
- What happens if a read misses because the SQLite row is absent or corrupted?
- **Decision**: The request falls through to static HTML or Python without repairing SQLite inline. Separate rebuild/backfill tooling handles recovery.

**Estimated effort**: 8–12 hours

**Canonical components touched**: Snapshot generation, moderation visibility, commit hooks

---

## Stage 4: PHP Thread Renderer

**Goal**: Implement the PHP-native rendering path for `/threads/{id}`, querying SQLite snapshots and generating HTML without invoking Python when static HTML is unavailable.

**Dependencies**:
- Stage 1 (thread contract)
- Stage 2 (SQLite snapshot access)
- Stage 3 (thread snapshots available in SQLite)
- Existing PHP rendering code in `php_host/public/index.php`
- Current thread HTML structure (reference from Python output)

**Expected changes**:
- New PHP functions in `php_host/public/index.php`:
  - `forum_php_native_read_thread_route(path: str) -> string|null` – check if path matches `/threads/{id}` and is eligible
  - `forum_php_native_load_thread_snapshot(thread_id: str) -> array|null` – query SQLite for thread snapshot
  - `forum_render_php_native_thread_page(snapshot: array) -> string` – generate HTML from snapshot
    - Render thread root (title, body, signature)
    - Render reply tree (nested, indented)
    - Render author metadata, tags, thread info
    - Match Python-generated HTML structure as closely as possible

- Update main request dispatcher in `index.php`:
  - Add thread eligibility check after the static HTML lookup and before the Python fallback path
  - If eligible, load snapshot and render native; if not, continue to Python path
  - Emit `X-Forum-Php-Native: HIT` header for native paths
  - Emit an operator-visible signal when a native-eligible thread request falls through because the SQLite snapshot is missing or unreadable

- Update `php_host/public/cache.php` (if needed):
  - Keep thread routes eligible for static HTML and preserve static HTML precedence over native PHP rendering

**Verification approach**:
- PHP syntax validation: `php -l php_host/public/index.php`
- Integration tests: `test_php_host_cache.py` extended with:
  - Thread route eligibility tests (bare `/threads/{id}` → native, `/threads/{id}?format=rss` → Python, authenticated → Python)
  - Static HTML precedence tests (warm static thread page wins over native snapshot)
  - Thread HTML structure comparison (native vs. Python output)
  - Missing/unreadable snapshot tests that verify fallthrough occurs without inline repair
- Manual smoke tests: request various thread IDs via PHP host, verify HTML structure and content

**Risks or open questions**:
- What if reply tree is very deep? Will PHP rendering be fast enough?
- **Decision**: Render full tree; monitor performance. If > 100ms, optimize later.
- How to handle signature display in PHP?
- **Decision**: Include signature metadata in snapshot; PHP renders as pre-formatted text (same as current).

**Estimated effort**: 10–14 hours

**Canonical components touched**: PHP request routing, thread HTML rendering, fallback logic, operator-visible headers/metrics

---

## Stage 5: Parity Testing & Validation

**Goal**: Ensure PHP-native thread rendering produces equivalent output to Python for representative thread structures, and verify no regression in non-native paths.

**Dependencies**:
- Stage 3 (Python snapshots built correctly)
- Stage 4 (PHP rendering implemented)

**Expected changes**:
- New test file: `tests/test_php_native_threads.py` with:
  - `test_php_native_thread_matches_python_structure()` – compare native vs. Python HTML structure
  - `test_php_native_thread_eligibility()` – verify eligible/ineligible requests routed correctly
  - `test_php_native_thread_moderation_visibility()` – hidden posts not rendered
  - `test_php_native_thread_fallback_when_snapshot_missing()` – graceful degradation
  - `test_php_native_thread_fallback_for_query_params()` – RSS and query-param requests use Python
  - `test_php_native_thread_static_html_precedence()` – static HTML wins when available
  - `test_php_native_thread_fallback_is_operator_visible()` – fallback headers/logging/counters are observable

- Update existing test files:
  - `tests/test_php_host_cache.py` – add thread-specific integration tests
  - `tests/test_php_native_reads.py` – add thread snapshot tests

- Test data: Create representative thread fixtures:
  - Simple flat thread (root + 5 replies)
  - Nested thread (root + reply + reply-to-reply, up to 3 levels)
  - Thread with moderation (some posts hidden, some marked)
  - Large thread (20+ replies to verify performance)

**Verification approach**:
- Run all new tests; verify pass rate > 95%
- Run full test suite; verify no regression
- Manual thread comparison (render same thread via Python and PHP, compare output)
- Performance check: measure PHP native rendering time for large thread (should be <50ms)
- Confirm fallback visibility works in practice: operators can distinguish native hits from static hits and from native-eligible fallback events

**Risks or open questions**:
- HTML output may differ due to formatting (whitespace, line breaks) — should we normalize for comparison?
- **Decision**: Use semantic HTML comparison (structure and content) rather than byte-exact matching. Allow minor formatting differences.

**Estimated effort**: 8–12 hours

**Canonical components touched**: Test infrastructure, parity validation, performance monitoring

---

## Stage 6: Operator Checklist & Documentation

**Goal**: Document deployment verification, monitoring, and troubleshooting for thread native rendering.

**Dependencies**:
- All prior stages complete
- Existing checklist: `php_host_native_read_performance_operator_checklist.md` (as template)

**Expected changes**:
- New file: `docs/plans/php_layer_thread_operator_checklist.md` with:
  - Pre-deployment verification (snapshot data looks correct, SQLite database size reasonable, SQLite support present in PHP runtime)
  - Deployment steps (backup snapshot database, run snapshot rebuild/backfill if needed, enable thread native rendering, monitor)
  - Post-deployment verification (static HTML precedence preserved, `X-Forum-Php-Native: HIT` header present on eligible native responses, latency improved)
  - Monitoring queries (SQLite snapshot freshness, thread snapshot count, operator-visible fallback frequency)
  - Troubleshooting (snapshot missing, stale data, rendering errors, unexpected fallback rate)
  - Rollback procedure (revert to Python-only if needed)

- Update main feature docs:
  - Update `php_host_native_read_performance_operator_checklist.md` with thread-specific notes
  - Update Step 4 summary (implementation notes for threads added)

**Verification approach**:
- Operator review: walkthrough checklist with deployment team
- Test rollback procedure
- Verify monitoring queries and fallback signals return expected data

**Estimated effort**: 3–5 hours

**Canonical components touched**: Operator documentation, monitoring, fallback observability

---

## Stage Summary & Timeline

| Stage | Title | Effort | Prerequisites | Output |
|-------|-------|--------|---------------|--------|
| 1 | Thread Read Contract | 2–4h | Step 2 | Thread contract doc |
| 2 | Thread Snapshot Schema & Access | 6–10h | Stage 1, design doc | Database schema, Python module |
| 3 | Python Snapshot Builder | 8–12h | Stage 1–2 | Thread snapshot generation |
| 4 | PHP Thread Renderer | 10–14h | Stage 1–3 | PHP native rendering code |
| 5 | Parity Testing | 8–12h | Stage 3–4 | Test suite, validated parity |
| 6 | Operator Checklist | 3–5h | Stage 1–5 | Deployment documentation |
| **Total** | | **37–57h** | | **Complete thread expansion** |

**Critical Path**:
- Stages 1, 2, 3 must be sequential (each depends on prior)
- Stage 4 depends on 1–3
- Stages 5 and 6 can overlap with 4 (testing can proceed as renderer is built)

---

## Verification Checkpoints

- **After Stage 1**: Thread contract document reviewed and approved
- **After Stage 2**: SQLite schema works, board index snapshot migrated successfully
- **After Stage 2**: SQLite schema works for thread snapshots and operator visibility is defined
- **After Stage 3**: Thread snapshots generated correctly, commit hook triggers refresh
- **After Stage 4**: PHP renderer produces HTML without Python when static HTML is absent, fallback works, and fallback events are visible to operators
- **After Stage 5**: Parity tests pass, no regressions in Python path
- **After Stage 6**: Operator can deploy and verify thread native rendering in production

---

## Rollback Plan

If any stage reveals critical issues:
- **Stage 1 block**: Stop; clarify contract, return to Step 2 refinement
- **Stage 2 block**: Revert SQLite changes; keep JSON files for board index (no feature loss)
- **Stage 2 block**: Disable thread native snapshot reads and continue serving static HTML/Python for threads (no feature loss)
- **Stage 3 block**: Disable thread snapshot generation in hook; board index still works
- **Stage 4 block**: Disable PHP thread path; requests fall through to Python (no feature loss)
- **Stage 5 block**: Run Stage 5 fixes before deployment; do not merge until tests pass
- **Stage 6 block**: Redeploy without thread native path (operator readiness issue, not code)

---

## Known Constraints & Assumptions

- PHP runtime has SQLite3 extension (or we fall back to JSON)
- PHP runtime has SQLite3 extension for the thread native-read feature; otherwise thread requests remain static/Python-only
- Thread snapshots fit in memory for rendering (validated in Stage 5)
- Post commit hook has access to repo root and SQLite database
- Thread nesting is well-defined (replies to replies, not circular)
- Moderation state is deterministic (same for all readers)
