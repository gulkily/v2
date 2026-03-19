1. Stage 1: Make the shared nav render a stable `My profile` slot before JavaScript enhancement
Goal: change the canonical shared header contract so the `My profile` position is present in the initial page HTML and does not appear later as a new nav item.
Dependencies: Approved Step 2; existing shared nav and page-shell rendering in `forum_web/templates.py`; current `data-profile-nav-link` contract.
Expected changes: extend the shared primary-nav and page-shell contract so `My profile` renders in a stable default state rather than a hidden late-added link; preserve the existing shared nav ordering and copy as much as possible; planned contracts such as `render_primary_nav(*, profile_nav_mode: str = "stable") -> str` or equivalent shared-header arguments only if needed.
Verification approach: render representative pages that use the shared header and confirm the initial HTML already contains a visible or layout-stable `My profile` slot with no hidden-placeholder-only behavior.
Risks/Open questions:
- Keep the default state understandable for users without a stored key.
- Avoid introducing a fake destination that feels broken before enhancement runs.
Canonical components/API contracts touched: shared primary nav; shared site header; shared page shell.

2. Stage 2: Narrow `profile_nav.js` to enhancing the stable nav slot instead of revealing it
Goal: preserve the current browser-derived profile-target and count behavior while removing the late-appearance layout shift.
Dependencies: Stage 1; existing browser asset `templates/assets/profile_nav.js`; current browser-held key and merge-notification logic.
Expected changes: update the nav asset so it enriches the pre-rendered `My profile` slot with the resolved href and optional count or badge rather than toggling hidden visibility as the primary behavior; keep the canonical `/profiles/<identity-slug>` target and notification behavior unchanged once browser data is available; planned contracts such as `enhanceProfileNav(doc = document) -> void` staying shared and reusable.
Verification approach: exercise the nav asset with and without stored-key data, confirm the nav text and href are enhanced correctly, and confirm the base slot remains stable when no target is available.
Risks/Open questions:
- Preserve current notification-count behavior without reintroducing visible nav shift.
- Keep non-browser import safety for the shared module tests.
Canonical components/API contracts touched: `profile_nav.js`; existing browser identity derivation helpers; shared `data-profile-nav-link` contract.

3. Stage 3: Add focused regression coverage for stable initial rendering and enhanced target behavior
Goal: lock in the no-shift nav contract across the shared header and browser enhancement path.
Dependencies: Stages 1-2.
Expected changes: extend shared-header and page tests to assert the initial HTML includes the stable `My profile` slot, update asset tests to assert enhancement changes href or count without relying on hidden-to-visible insertion, and keep coverage narrow to representative pages plus the nav asset; planned contracts such as `test_page_renders_stable_my_profile_slot()` and adjusted profile-nav asset assertions.
Verification approach: run focused header/page and asset tests, confirm the initial nav markup is stable, confirm browser enhancement still resolves the canonical profile link, and confirm no-target cases remain coherent.
Risks/Open questions:
- Avoid brittle assertions tied to incidental markup wording if the header copy changes later.
- Keep tests focused on rendering contract and enhancement outcome rather than visual pixel behavior.
Canonical components/API contracts touched: shared header/page tests; `profile_nav.js` asset tests; canonical profile-link behavior.
