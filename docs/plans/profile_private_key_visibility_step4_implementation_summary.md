## Stage 1 - Add dedicated account key page
- Changes:
  - added a dedicated `/account/key/` page that renders browser-stored key status plus private/public key textareas
  - reused the existing key viewer asset by making it work with either the legacy profile IDs or the new account-page IDs
  - added focused route coverage for the new page
- Verification:
  - `python -m pytest tests/test_account_key_page.py`
  - `python -m pytest tests/test_username_profile_route.py`
- Notes:
  - profile pages still render the existing key block in this stage; removal and canonical redirection are deferred to Stage 2

## Stage 2 - Move passive key viewing off public profiles
- Changes:
  - removed the passive key-material block and viewer script from public profile pages
  - added `view browser key` links to the username-update page, merge management page, and merge action page so account-related flows point to `/account/key/`
  - updated profile, profile-update, and merge-management assertions to reflect the new canonical destination
- Verification:
  - `python -m pytest tests/test_username_profile_route.py`
  - `python -m pytest tests/test_profile_update_page.py`
  - `python -m pytest tests/test_merge_management_page.py`
  - `python -m pytest tests/test_account_key_page.py`
- Notes:
  - compose and merge-signing flows still keep inline key controls because they are action-oriented signing surfaces, not passive key-viewing surfaces

## Stage 3 - Add regression coverage for the shared key viewer asset
- Changes:
  - added a focused asset test for `profile_key_viewer.js`
  - verified both the new account-page DOM targets and the legacy profile-target fallback behavior used during the transition
- Verification:
  - `python -m pytest tests/test_profile_key_viewer_asset.py`
- Notes:
  - this stage is test-only and locks in the generalized viewer contract without changing user-visible behavior
