## Stage 1 - shared read contract
- Changes:
  - Added the first shared cross-runtime read contract in [php_host_native_read_performance_shared_read_contract.md](/home/wsl/v2/docs/plans/php_host_native_read_performance_shared_read_contract.md).
  - Narrowed the v1 duplicated-path scope to one explicit route, `/`, with strict exclusions for query variants, personalized requests, and all write-sensitive paths.
  - Defined the Python-versus-PHP authority boundary, the prepared snapshot expectations, and the fallback/invalidation rules so later PHP-native work has a concrete spec.
- Verification:
  - Manual review against the approved Step 2 and Step 3 docs to confirm the contract stays within the planned allowlisted anonymous read boundary and leaves writes authoritative in Python.
- Notes:
  - This stage intentionally lands the spec first. No PHP-native rendering code is introduced until the shared contract is explicit enough to avoid accidental drift.

## Stage 2 - python-owned board index snapshot
- Changes:
  - Added [forum_core/php_native_reads.py](/home/wsl/v2/forum_core/php_native_reads.py) to build and write the first prepared PHP-native read artifact at `state/cache/php_native_reads/board_index_root.json`.
  - Matched the Stage 1 contract for `/` by emitting final-order visible thread rows plus explicit route targets, subject, preview, visible tags, reply counts, thread type labels, and summary counts.
  - Hooked [forum_cgi/posting.py](/home/wsl/v2/forum_cgi/posting.py) so every successful `commit_post(...)` refreshes the prepared snapshot after the post index is updated, keeping Python authoritative for invalidation.
- Verification:
  - `python3 -m unittest tests.test_php_native_reads`
  - `python3 -m unittest tests.test_request_operation_events tests.test_profile_update_submission tests.test_thread_auto_reply`
- Notes:
  - The dedicated Stage 2 tests pass.
  - The broader verification run exposed one unrelated existing failure in [tests/test_request_operation_events.py](/home/wsl/v2/tests/test_request_operation_events.py): `test_streamed_reindex_request_completes_operation_after_iterable_finishes` still expects older placeholder copy (`Refreshing forum data`) while the current streamed refresh page renders `Refreshing the forum...`.

## Stage 3 - php-native root renderer
- Changes:
  - Added a narrow PHP-native read path in [index.php](/home/wsl/v2/php_host/public/index.php) for anonymous `GET /` with no query string, cookies, or authorization headers.
  - Rendered the board index directly from `board_index_root.json`, preserving the shared-contract semantics for thread links, visible tags, preview text, reply counts, thread type labels, and stats.
  - Kept the existing fallback path intact: if the snapshot is missing, unreadable, or the request falls outside the allowlist, the PHP host still falls back to static HTML and then the Python CGI bridge.
- Verification:
  - `php -l php_host/public/index.php`
  - `python3 -m unittest tests.test_php_native_reads tests.test_php_host_cache`
- Notes:
  - Native `/` responses now emit `X-Forum-Php-Native: HIT`, which gives operators and tests a stable way to confirm the duplicated path is actually serving the request.

## Stage 4 - parity and operator verification
- Changes:
  - Extended [test_php_host_cache.py](/home/wsl/v2/tests/test_php_host_cache.py) with focused integration coverage proving that `/` can render from the snapshot without a working Python bridge and that query-bearing root requests do not take the native path.
  - Added [php_host_native_read_performance_operator_checklist.md](/home/wsl/v2/docs/plans/php_host_native_read_performance_operator_checklist.md) to document deployment checks, native-hit verification, freshness expectations after writes, and fallback recovery checks.
- Verification:
  - `python3 -m unittest tests.test_php_native_reads tests.test_php_host_cache`
- Notes:
  - The current parity coverage is intentionally semantic rather than full-page byte identity. It verifies route eligibility, visible board content, and fallback boundaries without making the PHP-native page shell brittle.
