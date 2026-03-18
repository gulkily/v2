## Stage 1
- Goal: extend the shared site shell and shared styling so non-homepage pages can adopt the homepage visual language without duplicating frame logic.
- Dependencies: approved Step 2; existing shared page renderer, base template, and site stylesheet; current homepage front-page shell work.
- Expected changes: generalize the shared shell so standard pages can use the same typography, spacing, link treatment, and calmer framing patterns while still allowing page-specific content regions; remove the homepage board-tag directory from the board-index template as part of the shared visual cleanup; planned helpers such as `render_page(..., page_variant: str = "default") -> str`.
- Verification approach: manually load `/`, one read page, and one write page to confirm the shared framing applies consistently and the homepage no longer shows the board-tag directory.
- Risks or open questions:
  - avoiding regressions on pages that still depend on compact status chips, tables, or compose-specific controls
  - deciding how much of the homepage shell should become site-wide versus remain homepage-specific
- Canonical components/API contracts touched: `forum_web/templates.py`; `templates/base.html`; `templates/assets/site.css`; `templates/board_index.html`.

## Stage 2
- Goal: restyle the main read surfaces so thread, post, moderation, instance, and profile pages match the new visual direction.
- Dependencies: Stage 1; existing read-page templates and route renderers.
- Expected changes: update the canonical read templates to use the refreshed shell conventions, calmer panel structure, and consistent metadata presentation while preserving current content hierarchy and links; planned templates include `thread.html`, `post.html`, `moderation.html`, `instance_info.html`, and `profile.html`.
- Verification approach: manually open representative pages for each read surface and confirm their routes, headings, metadata, and navigation still work while presenting in the refreshed style.
- Risks or open questions:
  - preserving clear information density on pages with more structured facts such as moderation and instance info
  - keeping thread/post reading comfortable without over-styling canonical text content
- Canonical components/API contracts touched: read-page HTML routes and templates; existing breadcrumb and metadata rendering helpers.

## Stage 3
- Goal: restyle the write and planning surfaces so compose, profile update, task priorities, and task detail pages align visually without changing behavior.
- Dependencies: Stage 1; existing compose/profile/task templates; current browser-signing and planning UI behavior.
- Expected changes: refresh the canonical interaction templates so compose and profile update keep the same form fields and browser-signing hooks, and task/priorities pages keep the same data and controls while matching the new style; planned templates include `compose.html`, `profile_update.html`, `task_priorities.html`, and `task_detail.html`.
- Verification approach: manually open each write/planning page, confirm forms and table controls still render correctly, and confirm existing data attributes and action links remain intact.
- Risks or open questions:
  - avoiding style changes that accidentally break compose JavaScript hooks or sortable task-table affordances
  - balancing visual consistency with the denser information needs of task planning screens
- Canonical components/API contracts touched: compose/profile/task HTML templates; browser-signing DOM hooks; task priorities table contract.

## Stage 4
- Goal: add focused regression coverage for the refreshed site-wide presentation and preserved navigation.
- Dependencies: Stage 1 through Stage 3.
- Expected changes: update or add tests that assert the shared shell markers and preserved key links on representative homepage, read, write, and planning pages, without overfitting to exact copy; planned coverage may extend existing page tests plus add one or two visual-structure checks where missing.
- Verification approach: run targeted unittest modules covering homepage, instance info, task priorities, compose, and any newly added page-structure tests, then manually click through the main routes for a final smoke pass.
- Risks or open questions:
  - keeping assertions stable enough for presentation coverage without making future copy edits noisy
  - deciding which pages need dedicated structure tests versus relying on existing route-level tests
- Canonical components/API contracts touched: representative HTML page responses across homepage, read pages, write pages, and planning pages; existing unittest coverage for those routes.
