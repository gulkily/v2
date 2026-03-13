## Stage 1
- Goal: establish the minimal read-only web app shell and canonical post reader.
- Dependencies: approved Step 2; existing canonical post files and record spec.
- Expected changes: add the smallest local web entrypoint, define deterministic post-loading and grouping rules, and introduce planned read helpers such as `load_posts(records_dir) -> [Post]` and `group_threads(posts) -> ThreadSet`; no write routes or API endpoints.
- Verification approach: start the local app, confirm it loads the sample repository without errors, and manually inspect that parsed threads and board tags match the raw files.
- Risks or open questions:
  - choosing ordering rules that later API work can reuse
  - keeping the initial app shell small enough
- Canonical components/API contracts touched: canonical post files in `records/posts/`; `docs/specs/canonical_post_record_v1.md`.

## Stage 2
- Goal: render the board-tag index view from the canonical repository state.
- Dependencies: Stage 1.
- Expected changes: add the board index page, deterministic thread listing by board tag, and navigation from the index to threads; planned helper such as `list_threads_by_board(posts) -> BoardIndex`.
- Verification approach: open the board index in a browser, confirm threads appear under expected board tags, and manually compare a few entries against the raw post files.
- Risks or open questions:
  - whether one root can appear under multiple board tags in the first cut
  - keeping index logic direct-read rather than drifting into durable indexing
- Canonical components/API contracts touched: canonical post files; direct-read board grouping rules.

## Stage 3
- Goal: render thread and permalink views over the sample dataset.
- Dependencies: Stage 2.
- Expected changes: add a thread page that shows root plus replies in deterministic order, add a post permalink page, and add simple navigation between index, thread, and post views; planned helpers such as `get_thread(thread_id) -> ThreadView` and `get_post(post_id) -> PostView`.
- Verification approach: browse from board index to a thread, confirm at least one root and replies render correctly, open a permalink for a specific post, and verify the displayed content matches the canonical file.
- Risks or open questions:
  - reply ordering policy may need refinement later
  - permalink handling should stay simple enough to align with the later API loop
- Canonical components/API contracts touched: canonical post files; direct-read thread and post lookup behavior.
