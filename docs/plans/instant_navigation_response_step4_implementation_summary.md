## Stage 1 - Define shared primary-nav pending contract
- Changes:
  - Added a shared browser enhancement asset in [primary_nav.js](/home/wsl/v2/templates/assets/primary_nav.js) that can mark a clicked primary-nav link as pending without changing normal link navigation.
  - Defined the initial contract around `[data-primary-nav]` and `[data-primary-nav-link]`, including safeguards for modified clicks and disabled unresolved links.
  - Added focused asset-level tests in [test_primary_nav_asset.py](/home/wsl/v2/tests/test_primary_nav_asset.py).
- Verification:
  - Ran `python -m unittest tests.test_primary_nav_asset`
  - Result: `OK`
- Notes:
  - This stage defines the shared client behavior only; page-shell rollout and prefetch remain in later stages.

## Stage 2 - Roll pending-state behavior onto Python-rendered pages
- Changes:
  - Extended the canonical Python nav renderer in [templates.py](/home/wsl/v2/forum_web/templates.py) so the shared header emits `data-primary-nav` and `data-primary-nav-link` hooks.
  - Added a dedicated Python page-shell script hook for [primary_nav.js](/home/wsl/v2/templates/assets/primary_nav.js) and exposed the asset through [asset_routes.json](/home/wsl/v2/templates/asset_routes.json) plus [page_shell_content.json](/home/wsl/v2/templates/page_shell_content.json).
  - Added a visible pending-link style in [site.css](/home/wsl/v2/templates/assets/site.css) and updated Python render/request tests in [test_primary_nav_active_state.py](/home/wsl/v2/tests/test_primary_nav_active_state.py), [test_board_index_page.py](/home/wsl/v2/tests/test_board_index_page.py), and [test_compose_thread_page.py](/home/wsl/v2/tests/test_compose_thread_page.py).
- Verification:
  - Ran `python -m unittest tests.test_primary_nav_active_state tests.test_board_index_page tests.test_compose_thread_page tests.test_primary_nav_asset`
  - Result: `OK`
- Notes:
  - Stage 2 intentionally keeps the new asset off PHP-served pages; the PHP shell rollout and prefetch allowlist remain in Stage 3.

## Stage 3 - Mirror shared nav behavior on PHP pages and add allowlisted prefetch
- Changes:
  - Extended the shared nav asset in [primary_nav.js](/home/wsl/v2/templates/assets/primary_nav.js) with a strict prefetch allowlist for `/`, `/activity/`, and `/tasks`, plus pointer/focus-triggered prefetch hooks that ignore non-allowlisted destinations.
  - Mirrored the shared primary-nav markup hooks in [index.php](/home/wsl/v2/php_host/public/index.php) and added the dedicated `primary_nav_script_source` include to the PHP page shell.
  - Added PHP-host assertions in [test_php_host_cache.py](/home/wsl/v2/tests/test_php_host_cache.py) and extended [test_primary_nav_asset.py](/home/wsl/v2/tests/test_primary_nav_asset.py) to cover allowlisted prefetch behavior.
- Verification:
  - Ran `python -m unittest tests.test_primary_nav_asset tests.test_php_host_cache.PhpHostCacheTests.test_php_host_serves_copy_field_asset_as_javascript tests.test_php_host_cache.PhpHostCacheTests.test_php_host_serves_primary_nav_asset_as_javascript tests.test_php_host_cache.PhpHostCacheTests.test_php_host_renders_primary_nav_hooks_and_script`
  - Result: `OK`
- Notes:
  - Personalized destinations such as `My profile` are intentionally excluded from prefetch in this slice.

## Stage 4 - Harden integrated nav-response verification
- Changes:
  - Added an explicit coexistence regression in [test_primary_nav_asset.py](/home/wsl/v2/tests/test_primary_nav_asset.py) proving `profile_nav.js` can still resolve `My profile` before `primary_nav.js` marks the same link pending.
  - Updated the remaining PHP snapshot assertion in [test_php_host_cache.py](/home/wsl/v2/tests/test_php_host_cache.py) to match the new shared primary-nav contract.
- Verification:
  - Ran `python -m unittest tests.test_primary_nav_asset tests.test_profile_nav_asset tests.test_primary_nav_active_state tests.test_board_index_page tests.test_compose_thread_page tests.test_php_host_cache`
  - Result: `OK` (`Ran 72 tests in 16.885s`)
- Notes:
  - The final verification pass covers both nav assets, Python-rendered pages, and the PHP host so the click-response contract is exercised across all shared-header paths in scope.
