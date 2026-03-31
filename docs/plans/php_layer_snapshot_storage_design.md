# PHP Native Reads – Snapshot Storage Design

## Recommendation: SQLite Database Over Filesystem JSON

Use a dedicated SQLite database (`state/cache/php_native_reads.sqlite3`) to store all PHP native read snapshots instead of individual JSON files.

## Rationale

### Problems with Filesystem JSON (Per-Entity Files)
- **Inode exhaustion**: Thousands of small JSON files consume inodes rapidly (limits depend on filesystem, but typically 1 file per thread/post/profile = thousands of inodes)
- **Directory scaling**: Reading directory contents becomes O(N) with large N
- **No atomic multi-entity updates**: If a post belongs to a thread, updating both snapshots isn't atomic; could leave them inconsistent
- **Harder to reason about**: No easy way to query "which snapshots are stale?" or "list all threads modified in last 5 minutes"
- **Backup/replication complexity**: Syncing thousands of small files is slower than one database file

### Benefits of SQLite
- **Already used**: Post index (`post_index.sqlite3`) and operation events use SQLite; proven pattern in codebase
- **Atomic transactions**: Multiple snapshot updates can be atomic (thread + replies refreshed together)
- **Indexing**: Can efficiently query snapshots by type, entity ID, or modification time
- **Vacuum/cleanup**: Easy to shrink the file, remove stale entries
- **Single file**: Easier to backup, replicate, version
- **Schema evolution**: Easier to add metadata columns (e.g., refresh_count, last_refresh_time, entity_type)

## Schema Design

```sql
CREATE TABLE IF NOT EXISTS php_native_snapshots (
    snapshot_id TEXT PRIMARY KEY,  -- {entity_type}/{entity_id}, e.g., "thread/abc123" or "profile/alice"
    entity_type TEXT NOT NULL,     -- "board_index", "thread", "post", "profile"
    entity_id TEXT,                -- NULL for board_index; thread_id, post_id, or profile_slug otherwise
    snapshot_json TEXT NOT NULL,   -- Full JSON snapshot (same structure as would be written to file)
    created_at TEXT NOT NULL,      -- ISO 8601 timestamp
    refreshed_at TEXT NOT NULL,    -- Last refresh time
    invalidated_by_post_id TEXT,   -- Which post invalidated this snapshot (if applicable)
    entity_version TEXT            -- Optional: content hash or version tag for change detection
);

CREATE INDEX IF NOT EXISTS snapshots_entity_type_id 
    ON php_native_snapshots(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS snapshots_refreshed_at 
    ON php_native_snapshots(refreshed_at);
```

## Migration Path

**Phase 1 (Current – Threads)**: Start fresh with SQLite
- Store board index snapshot (already exists as file) → migrate to SQLite
- Store new thread snapshots → SQLite

**Phase 2+ (Future routes)**: All snapshots use SQLite
- Profiles, posts, activity → all in same database

## Backward Compatibility

- Board index JSON file remains as-is for Phase 1 (snapshot at `state/cache/php_native_reads/board_index_root.json`)
- On-demand migration: If PHP host detects JSON file but no SQLite entry, migrate automatically
- Future: Can phase out JSON files entirely once all routes moved to SQLite

## Storage Efficiency

- **Single board index**: ~10–50 KB (one JSON file → one row)
- **Threads**: ~2–5 KB per thread × 1000 threads = ~2–5 MB total
- **Posts**: ~1–3 KB per post × 10000 posts = ~10–30 MB total
- **Profiles**: ~5–10 KB per profile × 100 profiles = ~0.5–1 MB total
- **Total SQLite database**: ~12–36 MB (single file) vs thousands of inodes

Much more efficient than thousands of small files, and single-file backup is straightforward.

## PHP Access Pattern

From `php_host/public/index.php`:

```php
function forum_read_php_native_snapshot($type, $id) {
    $db_path = $repo_root . '/state/cache/php_native_reads.sqlite3';
    $db = new SQLite3($db_path);
    $snapshot_id = $id ? "{$type}/{$id}" : $type;
    $result = $db->querySingle(
        "SELECT snapshot_json FROM php_native_snapshots WHERE snapshot_id = ?",
        $snapshot_id,
        $return_array = true
    );
    if ($result === false) {
        return null;  // Snapshot not found; fall back to Python
    }
    return json_decode($result['snapshot_json'], true);
}
```

Or, if PHP runtime doesn't have SQLite3 built in, use a fallback to the JSON file or fall back to Python.

## Invalidation & Refresh

In Python (`forum_core/php_native_reads.py`):

```python
def refresh_php_native_snapshots(connection: sqlite3.Connection, entity_type: str, entity_id: str, invalidated_by_post_id: str = None):
    snapshot_data = build_snapshot(entity_type, entity_id)  # Generate snapshot JSON
    snapshot_json = json.dumps(snapshot_data)
    snapshot_id = f"{entity_type}/{entity_id}" if entity_id else entity_type
    
    connection.execute("""
        INSERT OR REPLACE INTO php_native_snapshots 
        (snapshot_id, entity_type, entity_id, snapshot_json, created_at, refreshed_at, invalidated_by_post_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (snapshot_id, entity_type, entity_id, snapshot_json, datetime.utcnow().isoformat(), datetime.utcnow().isoformat(), invalidated_by_post_id))
```

## Operational Advantages

1. **Debugging**: `SELECT snapshot_id, refreshed_at FROM php_native_snapshots ORDER BY refreshed_at DESC LIMIT 10;` shows recently refreshed snapshots
2. **Cleanup**: Can garbage-collect stale snapshots: `DELETE FROM php_native_snapshots WHERE refreshed_at < datetime('now', '-7 days');`
3. **Monitoring**: `SELECT COUNT(*) FROM php_native_snapshots WHERE entity_type = 'thread';` shows how many thread snapshots are cached
4. **Integrity check**: `SELECT entity_type, COUNT(*) FROM php_native_snapshots GROUP BY entity_type;` validates cache state

## Decision

**Use SQLite for all PHP native read snapshots** (Phase 1 onward). Store board index in SQLite for consistency, and add all future snapshots to the same database. This avoids inode scaling issues and simplifies operational tooling.
