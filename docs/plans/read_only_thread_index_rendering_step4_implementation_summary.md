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
