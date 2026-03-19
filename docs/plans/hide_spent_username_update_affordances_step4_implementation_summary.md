## Stage 1 - derive username-update eligibility from repository state
- Changes:
  - Added `profile_can_update_username(...)` in [profiles.py](/home/wsl/v2/forum_web/profiles.py) so web read surfaces can determine whether the current profile is eligible to show `update username`.
  - Reused the existing visible-claim helper from [profile_updates.py](/home/wsl/v2/forum_core/profile_updates.py) so eligibility matches the current one-claim-per-signer backend rule.
  - Added focused coverage in [test_profile_update_visibility.py](/home/wsl/v2/tests/test_profile_update_visibility.py) for eligible and ineligible profile states.
- Verification:
  - `python -m unittest tests.test_profile_update_visibility`
- Notes:
  - This stage only derives the shared eligibility signal; the profile and merge pages still render the old affordances until Stage 2.
