## Stage 1 - username resolution helpers
- Changes:
  - Added latest-current-username token helpers in [profiles.py](/home/wsl/v2/forum_web/profiles.py) so the app can derive a conservative `/user/<username>` token from the current visible display name.
  - Added merged-profile username listing in [profiles.py](/home/wsl/v2/forum_web/profiles.py) so the joined page can later show all visible usernames in one resolved identity set.
  - Added a helper in [profiles.py](/home/wsl/v2/forum_web/profiles.py) that resolves a username route only when it maps unambiguously to one canonical merged profile under the current repository state.
- Verification:
  - Ran `python -m unittest tests.test_profile_update_page tests.test_merge_management_page tests.test_merge_management_api`.
  - Result: `Ran 7 tests ... OK`.
- Notes:
  - This stage only adds deterministic read helpers; it does not yet expose a `/user/<username>` route or change attribution links.

## Stage 2 - username route and joined profile page
- Changes:
  - Added the public `/user/<username>` route in [web.py](/home/wsl/v2/forum_web/web.py) and wired it to the same underlying resolved profile surface as `/profiles/<identity-slug>`.
  - Refactored profile rendering in [web.py](/home/wsl/v2/forum_web/web.py) so both route styles reuse one profile-page renderer instead of diverging.
  - Extended [profile.html](/home/wsl/v2/templates/profile.html) to show the public username route when one exists and to list visible usernames for the merged profile.
  - Updated [api_text.py](/home/wsl/v2/forum_web/api_text.py) so `/llms.txt` documents the new read surface.
- Verification:
  - Ran `python -m unittest tests.test_profile_update_page tests.test_merge_management_page tests.test_merge_management_api`.
  - Result: `Ran 7 tests ... OK`.
- Notes:
  - The joined page now exposes `/user/<username>` conservatively: if a latest current username is not unambiguous, the profile still renders through the identity-based route only.
