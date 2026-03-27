## Stage 1 - Thread self-profile render state
- Changes:
  - Extended `render_profile_page(...)` to accept a `self_request` render flag.
  - Passed the existing `self_request` state through `render_profile_for_request(...)`.
  - Kept username-route rendering explicit by passing `self_request=False` from `render_profile_by_username(...)`.
- Verification:
  - Ran `python -m unittest tests.test_my_profile_empty_state tests.test_profile_update_page`.
  - Confirmed the targeted profile and self-profile tests passed without changing visible behavior.
- Notes:
  - This stage only prepares the render boundary for the self-only action change in Stage 2.

## Stage 2 - Add self-profile username settings link
- Changes:
  - Reused the existing profile action row to compose self-profile-only action links.
  - Added a `username settings` link to `/profiles/<identity-slug>/update` when `self_request` is true and `profile_can_update_username(...)` is true.
  - Preserved existing public-profile behavior by keeping the new link out of non-self renders and leaving merge management intact.
- Verification:
  - Ran `python -m unittest tests.test_profile_update_page`.
  - Confirmed the existing profile page tests still pass after the action-row change.
- Notes:
  - The user-facing link text is `username settings` to match the request for a settings-oriented entry point from `My profile`.

## Stage 3 - Add self-profile visibility regression coverage
- Changes:
  - Extended `tests/test_profile_update_page.py` so profile page requests can pass a query string.
  - Added focused assertions proving eligible `?self=1` profile renders show `username settings`, ineligible `?self=1` renders hide it, and normal public profile renders continue to omit it.
- Verification:
  - Ran `python -m unittest tests.test_profile_update_page tests.test_my_profile_empty_state`.
  - Confirmed all targeted tests passed with the new self-profile coverage in place.
- Notes:
  - The regression coverage stays local to existing profile page tests and does not duplicate the separate shared CTA asset tests.

## Stage 4 - Present the self-profile link as a dedicated bar
- Changes:
  - Moved the self-profile username entry point out of the action row and into a dedicated full-width bar on the profile page.
  - Reused the existing `site-username-claim` presentation language so the self-profile bar matches the established `Account setup` treatment.
  - Updated profile page tests to assert the dedicated bar instead of an action-chip presentation.
- Verification:
  - Ran `python -m unittest tests.test_profile_update_page tests.test_my_profile_empty_state`.
  - Confirmed the eligible self-profile render shows the dedicated bar and the ineligible/public renders still hide it.
- Notes:
  - This was a presentation refinement requested after the initial action-row implementation; behavior and eligibility rules stayed unchanged.

## Stage 5 - Reuse the canonical account setup bar markup
- Changes:
  - Added a shared `render_username_claim_bar_html(...)` helper in [templates.py](/home/wsl/v2/forum_web/templates.py) so both account setup modules render from the same canonical markup.
  - Updated the mid-page self-profile module to use that shared helper, removing the extra custom wrapper treatment and matching the top module's copy and CTA text exactly.
  - Adjusted the profile-page tests to assert the canonical `Choose your username` button and shared body copy.
- Verification:
  - Ran `python -m unittest tests.test_profile_update_page tests.test_my_profile_empty_state`.
  - Confirmed the eligible self-profile bar matches the canonical account setup pattern and the visibility behavior is unchanged.
- Notes:
  - This change removes future drift risk between the header-level account setup surface and the profile-page version by centralizing the markup.
