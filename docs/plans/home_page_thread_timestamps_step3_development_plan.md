## Stage 1
- Goal: define one canonical server-rendered timestamp presentation contract that can produce a friendly relative label plus exact timestamp metadata from existing ISO-style time inputs.
- Dependencies: approved Step 2; existing timestamp parsing helpers in `forum_web/web.py`.
- Expected changes: add a shared timestamp-display helper layer for human-facing page rendering; planned contracts such as `parse_display_timestamp(raw_value: str) -> datetime | None`, `describe_timestamp_display(raw_value: str, *, now: datetime | None = None) -> TimestampDisplay`, and `render_timestamp_html(raw_value: str, *, css_class: str) -> str`; keep RSS/machine-readable date formatting separate.
- Verification approach: add focused helper tests for recent, older, invalid, and timezone-normalized timestamps and confirm the rendered output includes a friendly label plus exact `title` text.
- Risks or open questions:
  - choosing one exact tooltip format that works consistently for both commit-derived offsets and `Z`-style record timestamps
  - deciding how aggressively to collapse older timestamps into days versus weeks/months in the friendly label
- Canonical components/API contracts touched: shared timestamp formatter/render helper in `forum_web/web.py`; existing exact timestamp formatting paths that will be redirected to the shared contract.

## Stage 2
- Goal: add the canonical timestamp display to the home page thread rows using the same recency signal that currently drives board-index ordering.
- Dependencies: Stage 1; existing board index renderers; indexed root timestamps from `load_indexed_root_posts(...)`.
- Expected changes: extend board-index row rendering to resolve one thread-recency timestamp per visible row, render it in the row metadata, and preserve the current compact layout; planned contracts such as `thread_row_timestamp_text(thread_id: str, indexed_roots: dict[str, IndexedPostRow]) -> str | None` or equivalent board-index helper state passed into `render_board_index_thread_row(...)`.
- Verification approach: add board-index tests that confirm visible friendly timestamps appear, exact timestamps are present in `title`, and the row still suppresses empty/default metadata when timestamp data is unavailable.
- Risks or open questions:
  - clarifying whether the visible label should imply `updated`/`last activity` explicitly or remain a neutral timestamp token
  - keeping the row layout readable when tags, reply count, thread type, and timestamp all appear together
- Canonical components/API contracts touched: `visible_threads(...)`; `render_board_index_thread_rows(...)`; `render_board_index_thread_row(...)`; board-index CSS classes.

## Stage 3
- Goal: propagate the same timestamp display contract to the existing human-facing timestamp surfaces that already show dates so the site stops mixing raw, exact-only, and page-specific formats.
- Dependencies: Stage 1; current post, commit/activity, moderation, and operation renderers.
- Expected changes: update current human-facing timestamp renderers to use the shared helper for post cards, commit/activity cards, moderation records, and operation metadata where they already display time; preserve existing machine-readable feed output and non-time metadata structure.
- Verification approach: expand targeted page/render tests to confirm each migrated surface shows a friendly label with exact tooltip text and no longer emits raw timestamp strings where a user-facing timestamp already existed.
- Risks or open questions:
  - avoiding over-broad scope if some niche admin/debug surfaces are better left unchanged for this slice
  - deciding whether operation durations and start times should remain visually separate from state metadata after the timestamp text changes
- Canonical components/API contracts touched: `render_post_card(...)`; commit/activity card rendering; moderation card rendering; operation-event rendering; existing timestamp formatting helpers that become wrappers or are removed.

## Stage 4
- Goal: align the PHP/native board-index read model and regression suite with the home page timestamp contract so fast-path public reads stay consistent with Python-rendered output.
- Dependencies: Stage 2; existing board-index snapshot builder and PHP host cache tests.
- Expected changes: extend the board-index snapshot/read contract with the thread timestamp data needed for friendly-plus-exact display, update the PHP/native home page renderer or snapshot consumer to emit the same semantics, and add regression coverage for both Python and native/public paths.
- Verification approach: run targeted tests covering board-index page rendering, PHP/native snapshot shape, and PHP host cache behavior, then manually spot-check `/` on the standard render path and the native/public path when snapshot artifacts exist.
- Risks or open questions:
  - choosing a snapshot shape that is stable enough for native reads without duplicating too much presentation-specific data
  - keeping Python and PHP/native renders in sync if one path computes relative labels at request time and the other relies on stored snapshot values
- Canonical components/API contracts touched: `build_board_index_snapshot(...)`; board-index snapshot JSON contract; PHP/native board-index rendering path; tests for board index and PHP host cache behavior.
