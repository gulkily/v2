## Post Index Rebuild Rubber Duck Notes

### Symptom
Some requests were showing the full post-index rebuild timing pattern:

```text
post_index_load_posts
post_index_load_identity_context
post_index_commit_timestamps
post_index_upsert_all_posts
post_index_commit_sqlite
```

The expensive phase was typically `post_index_commit_timestamps`, which calls `git log --follow` across all post files during a full rebuild.

### Key observation
That timing pattern is the `rebuild_post_index(...)` path, not the normal incremental `refresh_post_index_after_commit(...)` path.

- Full rebuild path records `post_index_upsert_all_posts`
- Incremental refresh path records `post_index_upsert_touched_posts`

### Current understanding
- On a long-lived Python dev server, this should not be explained by the in-memory startup guard alone.
- `ensure_runtime_post_index_startup(...)` only runs once per process for a repo root.
- But indexed read helpers still call `ensure_post_index_current(...)` on ordinary requests.
- That means later requests can still trigger a full rebuild if the index is considered stale.

### Stale checks to watch
`ensure_post_index_current(...)` rebuilds when any of these are true:

- `indexed_post_count != expected_count`
- `indexed_head != current_head`
- `indexed_schema_version != POST_INDEX_SCHEMA_VERSION`

New posts and profile-related updates do create new git commits, but the normal write path is supposed to update the index metadata after a successful commit, so repeated rebuilds would suggest the metadata is not matching repo state later.

### Temporary diagnostic added
A warning log was added in `forum_core/post_index.py` inside `ensure_post_index_current(...)` before rebuilds.

It logs:

- `count_mismatch`
- `indexed_count`
- `expected_count`
- `head_mismatch`
- `indexed_head`
- `current_head`
- `schema_mismatch`
- `indexed_schema_version`
- `expected_schema_version`

Expected log shape:

```text
post index rebuild triggered for /path/to/repo: count_mismatch=... indexed_count=... expected_count=... head_mismatch=... indexed_head='...' current_head='...' schema_mismatch=... indexed_schema_version='...' expected_schema_version='3'
```

### Where to look
On the dev Python server, this warning should appear in the server process logs, usually the terminal running the server.

### Next step when it recurs
Capture one or two of those warning lines and inspect which stale-check predicate is firing. That should tell us whether the issue is:

- count drift
- head drift
- schema/version drift

without guessing from the rebuild timings alone.
