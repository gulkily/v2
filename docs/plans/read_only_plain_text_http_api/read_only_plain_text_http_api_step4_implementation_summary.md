## Stage 1 - API shell and text serializers
- Changes:
  - Added a dedicated plain-text API serializer module for deterministic read responses.
  - Added an `/api/` route shell to the existing WSGI app.
  - Added a shared repository-state loader so browser and API surfaces reuse the same canonical read path.
- Verification:
  - Called the WSGI app for `/api/` and confirmed a `200 OK` plain-text response with deterministic counts and the planned route list.
- Notes:
  - This stage intentionally stops at the API shell and serialization helpers; the actual `list_index`, `get_thread`, and `get_post` routes land in later stages.

## Stage 2 - list_index
- Changes:
  - Added the `/api/list_index` read endpoint to the existing WSGI app.
  - Defined a deterministic plain-text `list_index` response shape with command metadata, optional board filter reporting, and tab-separated thread rows.
  - Kept the endpoint on direct repository reads, with an optional `board_tag` query filter instead of a separate index store.
- Verification:
  - Called `/api/list_index` and confirmed a `200 OK` response with 9 deterministic thread rows matching the current repository state.
  - Called `/api/list_index?board_tag=wisdom` and confirmed a filtered `200 OK` response with 3 rows.
  - Called `/api/list_index?board_tag=missing` and confirmed a stable `400 Bad Request` plain-text error.
- Notes:
  - The response rows currently expose thread ID, subject, board tags, and reply count, which is enough for CLI and agent inspection in this slice.

## Stage 3 - get_thread and get_post
- Changes:
  - Added the `/api/get_thread` and `/api/get_post` read endpoints to the existing WSGI app.
  - Reused the canonical repository reader so thread and post API lookups stay aligned with the browser views.
  - Added stable plain-text `bad_request` and `not_found` handling for missing query parameters and unknown records.
- Verification:
  - Called `/api/get_thread?thread_id=oak-gate-quiet-work` and confirmed a `200 OK` response with `Record-Count: 4` and deterministic post order matching the repository grouping logic.
  - Called `/api/get_post?post_id=reply-009` and confirmed the response body matches the canonical post block in `records/posts/reply-009.txt`.
  - Called `/api/get_thread` without a query parameter and confirmed a stable `400 Bad Request` plain-text error.
  - Called `/api/get_post?post_id=missing` and confirmed a stable `404 Not Found` plain-text error.
- Notes:
  - `get_post` returns the canonical post block for the requested post.
  - `get_thread` returns a simple thread envelope followed by the canonical post blocks in deterministic thread order.
