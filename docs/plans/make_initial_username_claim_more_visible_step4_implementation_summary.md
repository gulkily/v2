## Stage 1 - derive and render the eligible-profile callout
- Changes:
  - Added `profile_username_claim_callout_text(...)` in [profiles.py](/home/wsl/v2/forum_web/profiles.py), derived directly from the existing profile eligibility rule.
  - Extended [test_profile_update_visibility.py](/home/wsl/v2/tests/test_profile_update_visibility.py) to cover the presence or absence of the shared callout text for eligible and ineligible profiles.
- Verification:
  - `python -m unittest tests.test_profile_update_visibility`
- Notes:
  - This stage only derives the shared callout signal; the profile header wiring lands in Stage 2.

## Stage 2 - render the eligible claim callout as a header CTA
- Changes:
  - Extended [templates.py](/home/wsl/v2/forum_web/templates.py) so page headers can optionally render one small hero action beneath the existing intro copy.
  - Updated [web.py](/home/wsl/v2/forum_web/web.py) so eligible profile pages render a header-level CTA chip that links to the existing `/profiles/<identity-slug>/update` flow using the shared callout text.
  - Extended [test_profile_update_page.py](/home/wsl/v2/tests/test_profile_update_page.py) to assert that eligible profiles show the prominent header CTA while ineligible profiles do not.
- Verification:
  - `python -m unittest tests.test_profile_update_page`
- Notes:
  - The CTA reuses the existing update route and does not change the existing one-claim eligibility rule.
