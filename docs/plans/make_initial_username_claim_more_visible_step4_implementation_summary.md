## Stage 1 - derive and render the eligible-profile callout
- Changes:
  - Added `profile_username_claim_callout_text(...)` in [profiles.py](/home/wsl/v2/forum_web/profiles.py), derived directly from the existing profile eligibility rule.
  - Updated [web.py](/home/wsl/v2/forum_web/web.py) so eligible profile pages append the one-time username-claim callout to the existing profile hero text.
  - Extended [test_profile_update_page.py](/home/wsl/v2/tests/test_profile_update_page.py) to assert that eligible profiles show the prominent callout and ineligible profiles do not.
  - Extended [test_profile_update_visibility.py](/home/wsl/v2/tests/test_profile_update_visibility.py) to cover the presence or absence of the shared callout text for eligible and ineligible profiles.
- Verification:
  - `python -m unittest tests.test_profile_update_visibility tests.test_profile_update_page`
- Notes:
  - This slice reuses the existing hero surface instead of adding a new profile-page section or separate onboarding component.
