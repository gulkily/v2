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
