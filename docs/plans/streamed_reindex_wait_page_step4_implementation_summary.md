## Stage 1 - Add same-request streamed reindex feedback
- Changes:
  - Updated the WSGI request lifecycle in `forum_web/web.py` so request-operation completion is deferred until iterable responses are fully consumed.
  - Added a streamed reindex wait response for covered GET routes on the long-lived Python host, with rebuild work staying inside the same request instead of using a background thread.
  - Added a runtime capability gate so CGI-style requests identified by `wsgi.run_once` stay on the existing non-streaming path.
  - Updated startup tests to cover streamed startup waits, cold-start waits, query-string preservation, and CGI-style fallback behavior.
- Verification:
  - `python -m unittest tests.test_post_index_startup tests.test_request_operation_events tests.test_wsgi_gateway tests.test_board_index_page tests.test_username_profile_route`
- Notes:
  - The current streamed response paints a minimal waiting shell and finishes by redirecting to the target path after rebuild completion.

## Stage 2 - Make the CGI/PHP fallback boundary explicit
- Changes:
  - Added gateway coverage showing that `forum_cgi/wsgi_gateway.py` buffers iterable chunks into one CGI response body instead of exposing true early streaming.
  - Kept the runtime gate in `forum_web/web.py` keyed to `wsgi.run_once`, so CGI/PHP remains on the non-streaming path without pretending streamed feedback is available there.
- Verification:
  - `python -m unittest tests.test_post_index_startup tests.test_request_operation_events tests.test_wsgi_gateway tests.test_board_index_page tests.test_username_profile_route`
- Notes:
  - This stage documents the current CGI/PHP limitation in behavior rather than attempting to redesign that gateway.
