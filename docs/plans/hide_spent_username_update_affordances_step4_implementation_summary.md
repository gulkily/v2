## Stage 1 - derive username-update eligibility from repository state
- Changes:
  - Added `profile_can_update_username(...)` in [profiles.py](/home/wsl/v2/forum_web/profiles.py) so web read surfaces can determine whether the current profile is eligible to show `update username`.
  - Reused the existing visible-claim helper from [profile_updates.py](/home/wsl/v2/forum_core/profile_updates.py) so eligibility matches the current one-claim-per-signer backend rule.
  - Added focused coverage in [test_profile_update_visibility.py](/home/wsl/v2/tests/test_profile_update_visibility.py) for eligible and ineligible profile states.
- Verification:
  - `python -m unittest tests.test_profile_update_visibility`
- Notes:
  - This stage only derives the shared eligibility signal; the profile and merge pages still render the old affordances until Stage 2.

## Stage 2 - hide ineligible username-update affordances on read surfaces
- Changes:
  - Updated [web.py](/home/wsl/v2/forum_web/web.py) so the profile action cluster and merge-management page only render `update username` when `profile_can_update_username(...)` is true.
  - Updated [merge_management.html](/home/wsl/v2/templates/merge_management.html) to accept the conditional update-link fragment from the route instead of always hardcoding the action.
  - Extended [test_profile_update_page.py](/home/wsl/v2/tests/test_profile_update_page.py) and [test_merge_management_page.py](/home/wsl/v2/tests/test_merge_management_page.py) to prove the link disappears once the viewed profile has a visible claim.
- Verification:
  - `python -m unittest tests.test_profile_update_page tests.test_merge_management_page`
- Notes:
  - The update page itself is unchanged; this stage only removes dead-end entry points from the public read surfaces.

## Stage 3 - lock in linked-identity affordance visibility behavior
- Changes:
  - Extended [test_profile_update_page.py](/home/wsl/v2/tests/test_profile_update_page.py) with a mixed linked-identity regression proving that another member identity's visible claim does not hide `update username` for the still-eligible profile being rendered.
  - Reused the spent-claim regressions from Stage 2 so the test suite now covers both sides of the rule: hide the link when the current profile is ineligible, keep it when only a linked peer is spent.
- Verification:
  - `python -m unittest tests.test_profile_update_page tests.test_merge_management_page`
- Notes:
  - No production logic changed in this stage; it locks in the intended profile-scoped eligibility behavior for linked identities.
