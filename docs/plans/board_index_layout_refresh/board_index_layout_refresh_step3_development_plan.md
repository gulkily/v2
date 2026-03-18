## Stage 1
- Goal: reshape the board-index render context so the homepage can drive a compact ZenMemes-style thread list and sidebar from real repository data.
- Dependencies: approved Step 2; existing `/` render path; current repository/thread grouping helpers.
- Expected changes: extend the board-index renderer with homepage-specific view data for ranked thread rows, compact metadata, grouped action links, and small sidebar modules derived from existing forum facts; planned helpers such as `build_board_index_page_context(posts, threads, moderation_state) -> dict[str, str]` and `render_board_index_thread_rows(threads, moderation_state) -> str`.
- Verification approach: load `/` against the current repo and a small test repo, confirm visible threads still come from repository-backed data, and confirm key links for compose, instance info, moderation, and task priorities remain present.
- Risks or open questions:
  - choosing compact metadata that reflects real fields without inventing unsupported concepts such as voting or merit
  - deciding which sidebar copy is static versus derived from repository state
- Canonical components/API contracts touched: `render_board_index()`; repository-backed thread visibility and link targets; existing homepage route `/`.

## Stage 2
- Goal: replace the current homepage structure and styling with the new calm, text-first layout while keeping the rest of the site stable.
- Dependencies: Stage 1; shared page shell and site stylesheet.
- Expected changes: update the homepage template and, if needed, add homepage-specific shell hooks so `/` can render header, primary thread list, sidebar, and footer regions without forcing the same structure onto thread/detail pages; planned helpers such as `render_page(..., page_shell_class: str = "", page_header_html: str | None = None) -> str`.
- Verification approach: open `/` on desktop and narrow-screen widths, confirm the new layout replaces the hero-and-card board index, and confirm thread links and action links remain usable with keyboard navigation.
- Risks or open questions:
  - keeping homepage-specific styling from regressing existing templates that share `base.html` and `site.css`
  - deciding whether the homepage should bypass the generic hero region or extend it in a minimal way
- Canonical components/API contracts touched: `templates/base.html`; `templates/board_index.html`; `templates/assets/site.css`; homepage link destinations.

## Stage 3
- Goal: add focused regression coverage and finish homepage readback checks for the refreshed layout.
- Dependencies: Stage 1 and Stage 2.
- Expected changes: update or add homepage-oriented tests so they assert the new structure and preserved destination links, while keeping current non-homepage behavior unchanged; planned coverage may include a homepage test module or extensions to existing board-index page tests.
- Verification approach: run targeted test modules for homepage-linked surfaces, then manually confirm `/` shows repository-backed threads, preserved key links, responsive collapse, and the intended reading order.
- Risks or open questions:
  - avoiding brittle assertions tied to exact copy where the visual rewrite may continue to evolve
  - deciding whether responsive behavior is covered only by manual smoke checks in this slice
- Canonical components/API contracts touched: homepage HTTP response at `/`; existing linked routes `/threads/<id>`, `/compose/thread`, `/instance/`, `/moderation/`, and `/planning/task-priorities/`; homepage-focused tests.
