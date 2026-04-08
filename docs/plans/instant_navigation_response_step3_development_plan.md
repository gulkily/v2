## Stage 1
- Goal: define one shared browser enhancement contract for immediate nav-pending feedback on primary-nav clicks.
- Dependencies: Approved Step 2 only.
- Expected changes: add one lightweight shared nav-enhancement asset and a minimal markup contract for primary-nav links so click feedback can be attached consistently; planned contracts such as `enhancePrimaryNav(...)`, a stable nav container selector, and per-link pending-state attributes or classes.
- Verification approach: add focused asset-level tests proving a clicked nav link enters a visible pending state immediately and non-primary links are ignored.
- Risks or open questions:
  - The pending state must stay truthful when users open links in a new tab or use modified clicks.
  - The shared contract should not collide with the existing `My profile` nav enhancement behavior.
- Canonical components/API contracts touched: shared primary nav in `forum_web/templates.py`; shared browser-asset pattern in `templates/assets`; existing `profile_nav.js` coexistence contract.

## Stage 2
- Goal: roll the shared pending-state behavior onto Python-rendered pages without changing normal navigation semantics.
- Dependencies: Stage 1.
- Expected changes: extend the Python page shell to load the shared nav-enhancement asset and annotate the canonical primary nav markup for click-state behavior; keep standard `<a href>` navigation unchanged.
- Verification approach: add request/render tests confirming Python-rendered pages include the nav-enhancement asset and the expected primary-nav markup hooks, then manually click through top-level nav pages to confirm immediate feedback with normal full-page loads.
- Risks or open questions:
  - The visual state must clear naturally on completed navigation without requiring persistent client state.
  - The enhancement must not interfere with unresolved or browser-resolved `My profile` targets.
- Canonical components/API contracts touched: `render_primary_nav(...)`; `render_page(...)`; shared site-header/page-shell asset loading contract.

## Stage 3
- Goal: extend the same behavior to PHP-served pages and add a narrow allowlist for pre-warming safe nav destinations.
- Dependencies: Stages 1-2.
- Expected changes: mirror the primary-nav markup hooks and shared asset loading in the PHP header path; add a small allowlist-driven prefetch contract for stable top-level GET destinations such as `/`, `/activity`, and `/tasks`; keep personalized destinations like `My profile` out of the initial prefetch path.
- Verification approach: add PHP-host request/cache tests confirming the shared nav markup and asset are present, plus asset-level tests proving only allowlisted destinations are prefetched.
- Risks or open questions:
  - Prefetch must stay conservative enough to avoid wasteful fetches or cache churn.
  - The allowlist needs to remain explicit so this slice does not quietly expand into broad speculative loading.
- Canonical components/API contracts touched: `php_host/public/index.php` primary-nav renderer and shell asset loading; shared nav-enhancement asset prefetch contract; canonical top-level GET route set.

## Stage 4
- Goal: harden the feature with focused regressions and cross-surface behavior checks.
- Dependencies: Stages 1-3.
- Expected changes: add targeted tests for immediate pending-state behavior, modified-click no-op behavior, Python/PHP header inclusion, allowlisted prefetch only, and coexistence with the `My profile` nav enhancement.
- Verification approach: run the focused browser-asset tests plus Python/PHP request tests, then manually verify immediate nav response on representative board, activity, task, and profile-related pages.
- Risks or open questions:
  - Tests should assert behavior contracts rather than brittle visual details.
  - Manual verification still matters because the core user value is perceptual responsiveness.
- Canonical components/API contracts touched: nav-enhancement asset tests; primary-nav render tests; Python and PHP shared-header regression suite.
