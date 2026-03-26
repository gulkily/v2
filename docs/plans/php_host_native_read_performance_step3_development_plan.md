## Stage 1
- Goal: Define one shared cross-runtime read contract for the first duplicated PHP-native public read slice.
- Dependencies: Approved Step 2; existing public read routes in `forum_web/web.py`; current PHP host entry path in `php_host/public/index.php` and `php_host/public/cache.php`.
- Expected changes: document the allowlisted route set, normalized route inputs, visibility and moderation rules, shared derived-data expectations, and cache invalidation boundaries as one canonical contract; planned contracts may include a dedicated spec artifact plus conceptual helpers such as `php_native_read_route(path: str) -> PhpNativeReadRoute | None` and `prepare_php_read_model(...) -> PreparedReadModel`.
- Verification approach: manual review of representative board/thread/post/profile cases to confirm the contract covers only hot anonymous reads and explicitly excludes personalized or write-sensitive behavior.
- Risks or open questions:
  - Need a contract narrow enough to implement in both runtimes without copying the full application.
  - Need to make route and visibility semantics explicit enough that PHP does not guess at Python behavior.
- Canonical components/API contracts touched: public read-route contract, canonical visibility rules, PHP host routing boundary.

## Stage 2
- Goal: Prepare one shared derived read-model or artifact boundary that PHP can consume without per-request raw repository interpretation.
- Dependencies: Stage 1; existing post-index and related derived read infrastructure in `forum_core/post_index.py` and current Python read flow.
- Expected changes: conceptually extend the Python-owned preparation layer to emit the minimum shared data needed for the allowlisted read routes, while keeping writes and invalidation authoritative in Python; planned contracts may include a prepared-read helper such as `build_php_public_read_snapshot(...) -> dict[str, object]` or a route-scoped artifact writer keyed by the Stage 1 contract.
- Verification approach: targeted checks that the prepared data remains deterministic for the same repository state and that relevant writes invalidate or refresh the affected prepared outputs.
- Risks or open questions:
  - Need to avoid making PHP depend on unstable Python-internal structures.
  - Need a refresh boundary that does not erase the current cache/static gains while adding a new prepared layer.
- Canonical components/API contracts touched: Python derived-read preparation, PHP-consumable artifact or snapshot contract, invalidation boundary from writes to reads.

## Stage 3
- Goal: Implement the first PHP-native renderer for the allowlisted hot public reads against the shared contract.
- Dependencies: Stages 1-2; current PHP host front controller and cache helper in `php_host/public/index.php` and `php_host/public/cache.php`.
- Expected changes: conceptually add a PHP-native read path that can match an allowlisted route, load the shared prepared data, and render the corresponding response without invoking Python CGI on that request; keep non-allowlisted routes and fallback behavior on the existing PHP-to-Python path.
- Verification approach: manual PHP-host smoke checks for covered route hits, uncovered route fallback, and behavior parity on representative anonymous reads; add focused PHP-host integration coverage where practical.
- Risks or open questions:
  - Need a clean fallback when prepared data is missing, stale, or unreadable.
  - Need to keep the first PHP-native renderer small enough that parity bugs remain tractable.
- Canonical components/API contracts touched: PHP front controller, PHP cache/static decision path, shared prepared-read contract from Stage 2.

## Stage 4
- Goal: Add parity and operator verification coverage for the duplicated read path before expanding scope.
- Dependencies: Stages 1-3; existing PHP-host and route-level test surfaces.
- Expected changes: extend automated coverage to compare covered anonymous read behavior across PHP-native and Python-backed paths, plus document a manual operator checklist for cache invalidation, covered-route latency, and fallback behavior; no database changes.
- Verification approach: run focused PHP-host and route tests, then manual PHP-host smoke checks confirming the allowlisted reads avoid per-request Python while non-allowlisted reads still work through the current path.
- Risks or open questions:
  - Test coverage must focus on stable route semantics and read-model parity rather than brittle full-page string identity.
  - Need a clear stop point so the first duplicated path proves the strategy without expanding immediately to every public route.
- Canonical components/API contracts touched: PHP-host test coverage, route-parity contract, operator verification and deployment expectations.
