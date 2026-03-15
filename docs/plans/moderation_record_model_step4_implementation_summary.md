## Stage 1 - moderation record and visible-state helpers
- Changes:
  - Added a shared moderation helper module for canonical moderation parsing, instance-local moderator authorization, and deterministic visible-state derivation.
  - Defined the minimal moderation record family around `hide`, `lock`, `pin`, and `unpin` and kept the record parser separate from the web and CGI entrypoints.
  - Added canonical repository documentation for `records/moderation/` so moderation stays git-native and inspectable.
- Verification:
  - Compiled the helper modules with `python3 -m py_compile forum_core/*.py`.
  - Loaded sample moderation records and confirmed repeated state derivation produced the same hidden, locked, and pinned sets.
  - Confirmed fingerprints not present in `FORUM_MODERATOR_FINGERPRINTS` are rejected consistently.
- Notes:
  - This stage intentionally stopped short of writing moderation records or exposing any public moderation view.

## Stage 2 - signed moderation write contract
- Changes:
  - Added a signed moderation submission path that verifies detached signatures, checks the moderator allowlist, validates target IDs, stores canonical records under `records/moderation/`, and commits them to git.
  - Added plain-text moderation preview and success bodies so moderation writes match the rest of the CGI-style command surface.
  - Exposed the write contract through `/api/moderate` and listed it on the API home surface.
- Verification:
  - Compiled the updated modules with `python3 -m py_compile forum_cgi/*.py forum_core/*.py forum_read_only/*.py`.
  - Submitted valid signed `pin`, `unpin`, `lock`, and `hide` actions against a disposable repository clone and confirmed canonical moderation files and git commits were created.
  - Confirmed an unauthorized moderator key returns `403 Forbidden` with a stable plain-text error.
- Notes:
  - Record IDs remain deterministic text chosen by the caller for this loop; content-derived moderation IDs can still be revisited later.

## Stage 3 - moderation log and read-time moderation effects
- Changes:
  - Added `get_moderation_log` plus deterministic cursor slicing and exposed the same log through `/moderation/`.
  - Updated board, thread, and post reads so hidden threads disappear from public listings, hidden posts render as placeholders, locked threads expose visible locked state, and pinned threads sort ahead of unpinned threads.
  - Extended reply validation and the signed compose route so locked or hidden targets reject new replies consistently instead of only hiding them in the reader.
  - Folded in two read-path fixes discovered during verification: the profile page now uses the updated repository-state tuple shape, and invalid moderation-log cursors return `400 Bad Request` in both API and HTML flows instead of surfacing a server error.
- Verification:
  - Compiled the updated modules with `python3 -m py_compile forum_cgi/*.py forum_core/*.py forum_read_only/*.py`.
  - In a fresh disposable repository clone, submitted signed moderation records for `pin root-002`, `lock root-002`, `hide reply-003`, and `hide root-001` using a generated moderator key allowlisted through `FORUM_MODERATOR_FINGERPRINTS`.
  - Confirmed `/api/get_moderation_log` returns stable reverse-chronological ordering, valid cursor pagination, and `400 Bad Request` for an unknown cursor.
  - Confirmed `/api/list_index?board_tag=general` hides `root-001`, puts pinned `root-002` first, and reflects the reduced visible reply count after hiding `reply-003`.
  - Confirmed `/api/get_thread?thread_id=root-002` and `/threads/root-002` show locked-thread state and a hidden-post placeholder, while `/api/get_thread?thread_id=root-001` and `/api/get_post?post_id=root-001` return `404 Not Found`.
  - Confirmed `/moderation/` renders the signed moderation log, `/compose/reply?thread_id=root-002&parent_id=root-002` returns `409 Conflict`, and direct `submit_create_reply(...)` calls reject replies to both the locked thread and the hidden thread.
  - Confirmed `/profiles/openpgp-708d998dd7e6b6bd05629b49676741195b215305` still returns `200 OK` after the moderation-path refactor.
- Notes:
  - Hidden replies currently remain visible as placeholders inside a visible thread, while hidden root posts suppress the entire thread from public read surfaces.
