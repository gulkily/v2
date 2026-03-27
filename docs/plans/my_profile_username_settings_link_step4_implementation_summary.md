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
