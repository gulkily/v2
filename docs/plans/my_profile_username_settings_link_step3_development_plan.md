## Stage 1
- Goal: expose one explicit self-profile render signal through the existing profile page path so the page can distinguish `?self=1` from normal public profile views.
- Dependencies: approved Step 2; existing `render_profile_for_request(...) -> render_profile_page(...)` flow.
- Expected changes: extend the profile-page render inputs with one conceptual self-profile flag such as `render_profile_page(..., self_request: bool, ...)`; keep route resolution unchanged and continue deriving username eligibility from the existing `profile_can_update_username(...)` helper.
- Verification approach: exercise profile rendering for the same identity with and without `?self=1` and confirm the render path can produce different action content without changing the rest of the page.
- Risks or open questions:
  - the self-profile marker must stay scoped to the request path and must not leak into username-route or general public profile rendering
  - the new render input should stay narrow so it does not create a second profile-page variant model
- Canonical components/API contracts touched: `render_profile_for_request(...)`; `render_profile_page(...)`; existing repository-state username eligibility helper.

## Stage 2
- Goal: add the self-only username-settings link to the profile action row when the viewed self-profile is currently eligible for the existing update flow.
- Dependencies: Stage 1; current `templates/profile.html` action cluster; existing `/profiles/<identity-slug>/update` route.
- Expected changes: extend the profile action-row composition so `?self=1` profile renders include a direct link to `/profiles/<identity-slug>/update` only when `profile_can_update_username(...)` is true; keep the link absent for ineligible self-profile views and for non-self public profile views; preserve unrelated actions such as merge management.
- Verification approach: manually render eligible self-profile, ineligible self-profile, and non-self public profile pages and confirm the username-settings link appears only in the eligible self-profile case with the existing update route as its target.
- Risks or open questions:
  - action-row ordering should stay clear if merge management is also present
  - the self-only link should not duplicate or conflict with the existing site-wide username-claim CTA behavior
- Canonical components/API contracts touched: `render_profile_page(...)`; `templates/profile.html`; existing `/profiles/<identity-slug>/update` contract.

## Stage 3
- Goal: add regression coverage for self-only visibility of the username-settings link.
- Dependencies: Stages 1-2; existing profile page and self-profile tests.
- Expected changes: add focused tests covering eligible self-profile renders, ineligible self-profile renders after a visible claim, and normal public profile renders for the same profile; assert that the link target remains `/profiles/<identity-slug>/update`.
- Verification approach: run the targeted profile rendering test modules that cover self-profile and username-update visibility behavior.
- Risks or open questions:
  - tests should assert the new self-only affordance without becoming brittle about unrelated page copy
  - coverage should complement existing CTA and update-page tests rather than duplicate them
- Canonical components/API contracts touched: `tests/test_profile_update_page.py`; `tests/test_my_profile_empty_state.py` or equivalent self-profile coverage; profile page render contract for action links.
