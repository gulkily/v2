## Stage 1
- Goal: define the canonical shared page-shell contract and remove the need for separate long-term layout paths.
- Dependencies: approved Step 2; existing `render_page(...)` flow; current `templates/base.html` outer shell.
- Expected changes: tighten the shared page renderer so one canonical header/footer/navigation/content-frame contract becomes the default for all primary routes; conceptually update shared render inputs such as `render_page(..., page_header_html: str | None = None, page_footer_html: str = "", page_shell_class: str = "") -> str` and any small shared helper signatures needed for reusable header/footer generation; no database changes.
- Verification approach: manually load representative routes and confirm the same outer shell structure appears around each page.
- Risks or open questions:
  - whether any homepage-specific or activity-specific header content needs a small shared variant instead of a single literal header block
  - avoiding a change that accidentally strips useful page-intro context from interior routes
- Canonical components/API contracts touched: `forum_web/templates.py:render_page`; `templates/base.html`; shared site header/footer/navigation contract.

## Stage 2
- Goal: migrate the current outlier pages onto the canonical shell while preserving their page-specific content.
- Dependencies: Stage 1; current board index and activity render paths; existing route templates.
- Expected changes: refit the board index and activity pages away from the separate front-page shell treatment, align any remaining template wrappers and CSS classes to the canonical layout, and keep route-specific content sections intact; planned conceptual touchpoints include `render_board_index() -> str`, `render_site_activity_page() -> str`, and template/CSS contract updates for page framing classes; no database changes.
- Verification approach: manually compare the homepage, activity page, a thread page, and a planning page to confirm they share one recognizable shell while keeping their own content blocks.
- Risks or open questions:
  - preserving useful homepage/action-link emphasis without keeping a second shell system
  - avoiding CSS regressions on pages that already fit the default shell
- Canonical components/API contracts touched: `/`; `/activity/`; existing route templates in `templates/`; shared `site.css` layout classes.

## Stage 3
- Goal: finish consistency pass, remove stale layout branches, and add focused regression coverage.
- Dependencies: Stages 1-2.
- Expected changes: clean up obsolete front-layout/front-header/front-footer pathways if they are no longer canonical, ensure the remaining primary routes still render correctly under the unified shell, and add targeted tests for representative pages so future changes do not reintroduce layout divergence; planned conceptual seams include page-render assertions in existing web tests and any small helper predicates needed for shell reuse; no database changes.
- Verification approach: run targeted tests for core page rendering and manually smoke-test the homepage, activity, thread, compose, profile, moderation, instance, task-detail, and task-priorities routes.
- Risks or open questions:
  - choosing test assertions that verify shell consistency without making tests brittle to copy changes
  - deciding whether any legacy CSS hooks should stay temporarily for safety even if no longer canonical
- Canonical components/API contracts touched: representative page render tests; primary web routes; shared layout CSS/template contract.
