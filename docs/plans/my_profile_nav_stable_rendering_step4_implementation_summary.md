## Stage 1 - Stable shared nav slot for My profile
- Changes:
  - Updated the shared primary nav in [templates.py](/home/wsl/v2/forum_web/templates.py) so `My profile` now renders in the initial HTML as a stable unresolved slot instead of a hidden late-added link.
  - Kept the existing shared nav ordering and `profile_nav.js` loading unchanged while marking the base slot as unresolved and non-interactive before enhancement.
  - Updated the board-index header test to lock in the new stable-slot contract.
- Verification:
  - `python -m unittest tests.test_board_index_page`
- Notes:
  - This stage only changes the initial shared-header contract. The browser asset still needs to be narrowed in the next stage so it enhances the stable slot instead of revealing it.
