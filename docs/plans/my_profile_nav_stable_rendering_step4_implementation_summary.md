## Stage 1 - Stable shared nav slot for My profile
- Changes:
  - Updated the shared primary nav in [templates.py](/home/wsl/v2/forum_web/templates.py) so `My profile` now renders in the initial HTML as a stable unresolved slot instead of a hidden late-added link.
  - Kept the existing shared nav ordering and `profile_nav.js` loading unchanged while marking the base slot as unresolved and non-interactive before enhancement.
  - Updated the board-index header test to lock in the new stable-slot contract.
- Verification:
  - `python -m unittest tests.test_board_index_page`
- Notes:
  - This stage only changes the initial shared-header contract. The browser asset still needs to be narrowed in the next stage so it enhances the stable slot instead of revealing it.

## Stage 2 - Narrow profile-nav enhancement to resolve the stable slot
- Changes:
  - Updated [profile_nav.js](/home/wsl/v2/templates/assets/profile_nav.js) so it now resolves the pre-rendered `My profile` slot by setting its href, state, and optional count instead of toggling hidden visibility.
  - Preserved the existing canonical profile-target and merge-notification behavior for users with a stored browser key.
  - Updated the profile-nav asset test to assert resolved-state enhancement rather than hidden-to-visible insertion.
- Verification:
  - `python -m unittest tests.test_profile_nav_asset tests.test_board_index_page`
- Notes:
  - Users without a stored key continue to see the unresolved stable slot from Stage 1; the next stage will lock that base-state behavior in more explicitly.
