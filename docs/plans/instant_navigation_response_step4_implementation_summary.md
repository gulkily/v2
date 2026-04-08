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
