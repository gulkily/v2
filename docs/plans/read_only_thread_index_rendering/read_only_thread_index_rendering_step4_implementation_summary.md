## Stage 1 - Web shell and canonical post reader
- Changes:
  - Added a small standard-library WSGI app and local run script for the read-only renderer.
  - Added deterministic canonical post loading and thread grouping helpers over `records/posts/`.
  - Added separate HTML and CSS templates so the app shell can render without embedding page content in code.
- Verification:
  - Ran `FORUM_PORT=8010 python3 scripts/run_read_only.py` and confirmed the local server started successfully.
  - Fetched `/` and confirmed the shell page rendered `17` posts, `5` threads, and `6` board tags from the repository state.
  - Fetched `/assets/site.css` and confirmed the separate stylesheet was served correctly.
  - Ran a direct repository check through `load_posts`, `group_threads`, and `list_board_tags` and confirmed the same `17 / 5 / 6` counts.
- Notes:
  - This stage intentionally stops at a shell page that proves direct repository loading; board index, thread view, and permalink rendering land in later stages.

## Stage 2 - Board-tag index view
- Changes:
  - Replaced the shell landing page with a board-tag index rendered directly from canonical post files.
  - Added deterministic grouping of thread roots by board tag and exposed thread links for the next stage.
  - Added a dedicated board index template and extended the site styling for board sections and thread cards.
- Verification:
  - Ran `FORUM_PORT=8011 python3 scripts/run_read_only.py` and fetched `/`.
  - Confirmed the board index rendered all `6` board tags and grouped thread roots under the expected sections.
  - Verified direct grouping output from `list_threads_by_board` matched the page, including `general -> root-001, root-002, root-004` and `wisdom -> root-002, root-005`.
- Notes:
  - Thread links intentionally point at routes that will be implemented in the next stage.

## Stage 3 - Thread and permalink views
- Changes:
  - Added direct-read thread pages at `/threads/{thread-id}` and permalink pages at `/posts/{post-id}`.
  - Added thread and post templates, body rendering, breadcrumbs, and post cards so the board index now links to working pages.
  - Added deterministic post and thread lookup helpers over the existing canonical repository state.
- Verification:
  - Ran `FORUM_PORT=8012 python3 scripts/run_read_only.py` and fetched `/`, `/threads/root-002`, and `/posts/reply-009`.
  - Confirmed `/threads/root-002` rendered the root post plus all three replies from the canonical files.
  - Confirmed `/posts/reply-009` rendered a permalink page with links back to `root-004` and the board index.
  - Confirmed the board index still linked to working thread routes after the new pages were added.
- Notes:
  - Reply ordering remains the simple deterministic repository order chosen for this loop and may be refined later if the data model grows.
