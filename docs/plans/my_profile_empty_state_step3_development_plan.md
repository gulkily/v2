1. Stage 1: Recognize the unpublished self-profile case on the canonical profile route
Goal: let `/profiles/<identity-slug>` distinguish between an unknown profile slug and a signed user’s own identity slug that has not published visible profile data yet.
Dependencies: Approved Step 2; existing `My profile` navigation target contract; current profile lookup flow in `forum_web/profiles.py` and `forum_web/web.py`.
Expected changes: extend the profile-route decision path so it can detect a narrow pre-publication self-profile state instead of always falling through to the generic missing-resource response; keep the published-profile summary contract unchanged; planned contracts such as `find_profile_summary(...) -> ProfileSummary | None` staying intact plus a new conceptual helper like `resolve_unpublished_profile_state(identity_id, repo_root, posts) -> UnpublishedProfileState | None` if needed.
Verification approach: request the canonical profile route for a slug backed only by browser-derived identity context or bootstrap identity material, confirm the route can classify the unpublished self-profile case separately from a truly unknown slug, and confirm published profiles still resolve normally.
Risks/Open questions:
- Keep the detection rule narrow so unrelated missing slugs still render the generic not-found experience.
- Avoid expanding this stage into broader onboarding or identity bootstrap redesign.
Canonical components/API contracts touched: canonical `/profiles/<identity-slug>` route; profile lookup/read-model boundary; generic missing-resource fallback contract.

2. Stage 2: Render a profile-aware empty state on `/profiles/<identity-slug>`
Goal: replace the generic “This record could not be located” result with a meaningful first-visit `My profile` page for the unpublished self-profile case.
Dependencies: Stage 1; existing shared page shell in `render_page(...)`; current profile template and page-copy patterns.
Expected changes: add one profile-specific empty-state rendering path that explains there are no published signed posts or profile updates yet and offers the smallest useful next action; preserve the same canonical route and standard page framing; planned contracts such as `render_empty_profile(...) -> str` or equivalent route-local rendering helper without changing published-profile rendering behavior.
Verification approach: open `/profiles/<identity-slug>` for the unpublished self-profile case, confirm the page uses the normal shell, confirm the copy explains the empty unpublished state, and confirm published profiles still render the existing profile page instead of the empty state.
Risks/Open questions:
- Choose next-action copy that is useful without committing the feature to a larger setup flow.
- Keep the empty state clearly personal/private in tone so it does not look like a broken public profile.
Canonical components/API contracts touched: canonical profile page route; shared page shell/header/nav; profile-page rendering contract.

3. Stage 3: Add focused regression coverage for unpublished self-profile and existing profile behavior
Goal: lock in the new empty-state contract without weakening current published-profile or generic missing-resource behavior.
Dependencies: Stages 1-2.
Expected changes: add route/page tests for the unpublished self-profile case, preserve or extend tests proving published profiles still render normally, and add at least one regression asserting unrelated missing profile slugs still use the generic missing-resource response; planned contracts such as `test_my_profile_route_renders_empty_state_before_first_post()` and `test_unknown_profile_slug_still_returns_missing_resource()`.
Verification approach: run the focused profile-route test set, confirm the unpublished self-profile case no longer shows the generic missing-record page, confirm normal profiles still show the existing profile content, and confirm true unknown slugs still produce the current not-found experience.
Risks/Open questions:
- Keep tests aligned to behavioral contract rather than brittle page-copy details beyond the core message.
- Avoid over-coupling tests to browser-only nav derivation when this slice is about route outcome.
Canonical components/API contracts touched: profile-route tests; canonical missing-resource behavior; published-profile rendering contract.
