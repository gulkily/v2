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
