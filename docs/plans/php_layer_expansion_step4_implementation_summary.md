# Step 4 - Implementation Summary: PHP Native Thread Detail Pages

## Changes

- Added SQLite-backed thread snapshot storage in `forum_core/php_native_reads_db.py` with snapshot rows plus `php_native_read_counters` for operator-visible fallback accounting.
- Extended `forum_core/php_native_reads.py` to:
  - build SQLite-backed thread snapshots for `/threads/{id}`,
  - resolve affected thread IDs deterministically from touched write paths,
  - refresh or delete thread snapshot rows after authoritative writes,
  - and support explicit snapshot backfill via `rebuild_php_native_thread_snapshots(...)`.
- Updated `forum_cgi/posting.py` so the shared post-commit path passes touched paths into PHP-native snapshot refresh.
- Added `./forum rebuild-php-native-snapshots` in `scripts/forum_tasks.py` for operator-driven backfill/recovery.
- Extended `php_host/public/index.php` so:
  - board-index native reads continue using the existing JSON snapshot path,
  - static HTML remains preferred for thread reads,
  - thread native reads use SQLite snapshots after static misses,
  - and native snapshot misses increment SQLite counters and emit `X-Forum-Php-Native-Fallback: snapshot-missing`.
- Added coverage in `tests/test_php_native_reads.py` and `tests/test_php_host_cache.py` for:
  - thread snapshot shape,
  - deterministic invalidation resolution,
  - SQLite backfill,
  - native thread hits,
  - static HTML precedence,
  - and counted fallback behavior.

## Verification

- `python -m unittest tests.test_php_native_reads`
- `python -m unittest tests.test_php_host_cache`
- `python -m unittest tests.test_task_thread_pages`
- `php -l php_host/public/index.php`
- `python scripts/forum_tasks.py rebuild-php-native-snapshots --help`

## Notes

- The existing board-index native-read artifact remains JSON-backed in this slice.
- New thread native reads use SQLite only.
- Thread fallback does not rebuild snapshots inline; rebuild/backfill remains operator-driven.
