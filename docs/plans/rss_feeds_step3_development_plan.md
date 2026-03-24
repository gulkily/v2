## Stage 1
- Goal: define one shared RSS rendering layer and scope-specific feed loaders for activity, board index, and thread views.
- Dependencies: approved Step 2; existing repository-backed read helpers for activity events, visible threads, and thread loading.
- Expected changes: add a small RSS helper layer in `forum_web/web.py` (or a nearby shared module) that can build channel metadata and item XML from current read-side objects; planned contracts such as `render_rss_feed(*, title: str, description: str, link: str, items: list[FeedItem]) -> bytes`, `load_activity_feed_items(repo_root, *, view_mode: str, page: int) -> list[FeedItem]`, `load_board_feed_items(repo_root, *, board_tag: str | None) -> list[FeedItem]`, and `load_thread_feed_items(thread_id: str) -> list[FeedItem]`; no database changes.
- Verification approach: add helper-level tests that build feeds from representative activity, board, and thread data and confirm the XML contains the expected titles, canonical links, and visible item ordering.
- Risks or open questions:
  - keeping one small feed item shape that can cover mixed activity entries and thread/reply entries
  - choosing a minimal channel metadata contract without drifting into feed-specific product copy
- Canonical components/API contracts touched: `load_activity_events(...)`; `visible_threads(...)`; thread/post loading helpers; new shared RSS renderer.

## Stage 2
- Goal: expose RSS HTTP responses for the current canonical read scopes without introducing a separate feed-only routing model.
- Dependencies: Stage 1; current `/activity/`, `/`, and `/threads/{thread-id}` read routes; existing board-tag filtering behavior in the read model.
- Expected changes: extend routing so the current read surfaces can return RSS for the same scope, likely through format/query handling or narrowly paired feed endpoints; support overall activity, board-index scope, optional `board_tag`-filtered board scope, and individual thread scope; planned contracts such as `request_wants_rss(path: str, query_params: dict[str, list[str]]) -> bool`, `render_activity_rss(view_mode: str, page: int) -> bytes`, `render_board_index_rss(board_tag: str | None) -> tuple[str, bytes]`, and `render_thread_rss(thread_id: str) -> tuple[str, bytes]`.
- Verification approach: manually request the HTML and RSS forms of `/activity/`, `/`, `/?board_tag=...` (or the chosen board-scope URL), and `/threads/{thread-id}`; confirm RSS responses use `application/rss+xml`, visible items match the page scope, and invalid board/thread requests still fail predictably.
- Risks or open questions:
  - deciding the smallest discoverable URL shape for board-specific feeds when there is not yet a dedicated board HTML page
  - keeping HTML and RSS route handling straightforward instead of adding brittle branching
- Canonical components/API contracts touched: `/activity/`; board index route; `/threads/{thread-id}`; WSGI route dispatch and content-type handling.

## Stage 3
- Goal: add feed discovery links to the existing HTML surfaces so users can find the right subscription URL from the page they are reading.
- Dependencies: Stage 2; existing page rendering shell and page-specific templates/context builders.
- Expected changes: extend the relevant HTML responses with RSS discovery metadata and a small visible subscription affordance on activity, board index, and thread pages; planned contracts such as `render_feed_link_chip(feed_href: str) -> str` and `render_page(..., alternate_feed_href: str | None = None)` or an equivalent page-head hook for `<link rel="alternate" ...>`.
- Verification approach: manually load the affected HTML pages, confirm each one exposes the correct feed URL for its scope, and add focused assertions that the rendered HTML includes the alternate-feed metadata and visible subscription link.
- Risks or open questions:
  - keeping the discovery affordance visible but not noisy on already dense pages
  - ensuring board-filtered pages advertise the filtered feed URL rather than the unfiltered root feed
- Canonical components/API contracts touched: shared page shell/template; activity page rendering; board index rendering/context; thread page rendering/context.

## Stage 4
- Goal: lock RSS behavior into focused regression coverage across XML output, scope filtering, and route compatibility.
- Dependencies: Stages 1-3; existing page and route tests.
- Expected changes: add targeted tests for RSS content type, XML structure, canonical item links, moderation-aware visibility, activity-filter handling, board-tag feed scope, thread reply ordering, and feed discovery markup on the related HTML pages.
- Verification approach: run targeted tests for the RSS helpers and affected route/page suites, then manually open the main feed URLs in a browser or feed reader-compatible viewer to confirm they render as valid feed documents.
- Risks or open questions:
  - avoiding brittle XML string assertions while still checking meaningful feed semantics
  - keeping fixture history small enough that activity and thread feed expectations stay readable
- Canonical components/API contracts touched: RSS helper tests; activity page tests; board index tests; thread page tests; route/content-type coverage.
