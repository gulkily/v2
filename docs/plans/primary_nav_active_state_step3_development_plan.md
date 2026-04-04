## Stage 1
- Goal: extend the shared header/nav contract so server-rendered pages can declare one active top-level section in the primary nav.
- Dependencies: approved Step 2; existing shared header and primary-nav rendering in [`forum_web/templates.py`](/home/wsl/v2/forum_web/templates.py); existing shared shell content in [`templates/page_shell_content.json`](/home/wsl/v2/templates/page_shell_content.json).
- Expected changes: add one conceptual active-section input to the shared primary-nav and header render path; preserve the current nav labels and ordering; define one stable selected-state marker for the active nav item rather than relying on page-local copy or body context.
- Verification approach: render representative shared-header pages and confirm the initial HTML can mark exactly one top-level nav item as active while leaving the rest unchanged.
- Risks or open questions:
  - the active-state contract should stay narrow and avoid turning the shared shell into a general route parser
  - the selected-state markup should remain compatible with both Python and PHP-served shells
- Canonical components/API contracts touched: `render_primary_nav(...)`; `render_site_header(...)`; shared page-shell/nav content contract.

## Stage 2
- Goal: map existing read routes to the correct top-level nav section, including keeping `Activity` selected for all `/activity/` filtered subsection views.
- Dependencies: Stage 1; current page render paths in [`forum_web/web.py`](/home/wsl/v2/forum_web/web.py); current PHP shared shell in [`php_host/public/index.php`](/home/wsl/v2/php_host/public/index.php).
- Expected changes: extend the canonical route render paths so top-level pages pass the correct active section into the shared header; treat `/activity/` and its `view=all|content|moderation|code` subsections as one parent `Activity` section; keep page-local activity filter chips separate from top-level nav selection.
- Verification approach: manually render home, compose, instance, activity, and one activity filtered subsection through the shared shell and confirm the correct top-level nav item is selected in each case.
- Risks or open questions:
  - route-to-section mapping should stay centralized enough that new pages do not drift into inconsistent behavior
  - moderation redirects into activity should preserve the top-level `Activity` selection without introducing a second selected-state model
- Canonical components/API contracts touched: top-level page render paths in `forum_web/web.py`; shared header contract on the PHP read path; activity page route and filter-view contract.

## Stage 3
- Goal: style and lock the active-nav behavior into regression coverage for both shared shells and activity subsections.
- Dependencies: Stages 1-2; existing shared-nav CSS in [`templates/assets/site.css`](/home/wsl/v2/templates/assets/site.css); existing route/page tests for board, compose, activity, and PHP host shells.
- Expected changes: add one shared nav active-state style that is visually clear without conflicting with the existing activity filter-chip selection pattern; extend focused route-level tests to assert the selected nav item on representative pages and activity subsection views; add PHP-hosted coverage for the same top-level selection behavior where applicable.
- Verification approach: run the focused shared-shell and activity page test modules and confirm they assert both top-level nav selection and continued activity subsection selection.
- Risks or open questions:
  - active-nav styling should remain distinct from disabled or unresolved nav states such as the `My profile` placeholder
  - tests should assert the shared nav contract without becoming brittle about unrelated header formatting
- Canonical components/API contracts touched: `site.css` shared nav styling; route/page tests for board, compose, and activity pages; PHP host shell regression tests.
