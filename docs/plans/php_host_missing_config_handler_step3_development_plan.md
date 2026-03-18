1. Stage 1: Isolate the missing-config response contract
- Goal: separate missing-config detection from raw inline output so the PHP adapter has one canonical response path for this failure.
- Dependencies: Approved Step 2; existing missing-config detection in `php_host/public/index.php`.
- Expected changes: introduce one small PHP helper boundary for the missing-config case, such as `forum_render_missing_config_page(string $expectedPath): never` or an equivalent response builder; keep status `500` and explicit failure semantics unchanged.
- Verification approach: manually request the PHP entrypoint with no `forum_host_config.php` present and confirm the same failure condition now routes through the dedicated handler.
- Risks or open questions:
  - keep the helper narrow so this does not become a generic PHP error framework
  - confirm the page exposes only the path detail that is acceptable for operator diagnostics
- Canonical components/API contracts touched: `php_host/public/index.php`; required `forum_host_config.php` contract.

2. Stage 2: Add the polished admin-facing diagnostic page
- Goal: replace the raw two-line output with a deliberate, readable diagnostic surface for operators.
- Dependencies: Stage 1 response boundary.
- Expected changes: add structured page copy covering the missing file, expected path, recovery command, and next-step guidance; add lightweight inline presentation styling within the PHP-host surface so the page feels intentional without introducing a broader shared design system.
- Verification approach: manually load the missing-config page and confirm it renders a readable layout with the missing include name, expected path, `./forum php-host-setup` guidance, and a clear distinction between config failure and application failure.
- Risks or open questions:
  - avoid visual scope creep into a general PHP-host admin console
  - keep the page readable on both desktop and narrow/mobile widths
- Canonical components/API contracts touched: `php_host/public/index.php`; existing `./forum php-host-setup` operator workflow.

3. Stage 3: Link the page back to the supported install docs
- Goal: make the recovery loop complete from the failure page itself.
- Dependencies: Stage 2 page content.
- Expected changes: add one canonical documentation reference from the missing-config page to the PHP-host installation guide, keeping the setup command as the primary action and the docs as secondary support.
- Verification approach: manually confirm the rendered page includes the intended installation-guide reference and that the guidance order stays obvious: fix config first, then consult docs if needed.
- Risks or open questions:
  - ensure the docs link/reference remains valid in deployed PHP-host layouts
- Canonical components/API contracts touched: `php_host/public/index.php`; `docs/php_primary_host_installation.md`.

4. Stage 4: Regression coverage for missing-config rendering
- Goal: lock the new failure behavior down with focused tests.
- Dependencies: Stages 1-3.
- Expected changes: add or extend focused tests around the PHP host entrypoint so a missing `forum_host_config.php` asserts status `500` plus stable page content for the missing-config title, expected path, and recovery guidance.
- Verification approach: run the focused PHP-host test file(s) covering the new missing-config case and confirm both behavior and key copy fragments are stable.
- Risks or open questions:
  - choose assertions that are specific enough to prevent regression without making wording changes unnecessarily brittle
- Canonical components/API contracts touched: PHP-host entrypoint test coverage; missing-config response contract.
