1. Goal: expose one deterministic “eligible to update username” signal for the viewed profile in the shared profile/read context.
Dependencies: approved Step 2; existing profile summary and loaded profile-update records.
Expected changes: add one narrow helper or summary field such as `profile_can_update_username(identity_id, identity_context, profile_updates) -> bool` or `ProfileSummary.can_update_username: bool`; derive the state from current visible repository rules for the viewed profile only.
Verification approach: build/read fixtures for eligible and ineligible profiles, then confirm the derived state flips deterministically.
Risks or open questions:
- the state must stay grounded in repository-state rules only, not client/browser ownership state
- mixed linked-identity cases must still distinguish one viewed profile being eligible while another is not
Canonical components/API contracts touched: shared profile read helper/context; profile summary data passed to web profile surfaces.

2. Goal: hide `update username` on the existing profile and merge-management pages whenever the viewed profile is not eligible to update.
Dependencies: Stage 1; current `/profiles/<identity-slug>` and `/profiles/<identity-slug>/merge` templates/routes.
Expected changes: conditionally suppress the `update username` links in the profile action cluster and merge-management navigation when the eligibility signal is false; leave all other controls unchanged and do not alter `/profiles/<identity-slug>/update` itself.
Verification approach: manually render profile and merge pages for eligible and ineligible profiles and confirm the link appears only for eligible cases.
Risks or open questions:
- the UI should remain stable when a canonical merged profile is viewed through different member-identity routes
- hiding the link should not accidentally suppress unrelated actions such as `manage merges`
Canonical components/API contracts touched: `render_profile_page(...)`; `render_merge_management_page(...)`; `templates/profile.html`; `templates/merge_management.html`.

3. Goal: lock in regression coverage for eligible and ineligible affordance visibility across linked-identity scenarios.
Dependencies: Stages 1-2; existing profile-page and merge-management tests.
Expected changes: add focused tests showing that ineligible profiles hide `update username`, eligible profiles still show it, and linked/merged profiles obey the rule per viewed profile under repository-state eligibility rather than per browser session.
Verification approach: run targeted profile-page and merge-management test modules with fixtures covering single-identity, ineligible, and linked mixed-state cases.
Risks or open questions:
- tests must distinguish different repository-state reasons for ineligibility without drifting into client-side ownership logic
- coverage should stay small and avoid duplicating broader username-resolution behavior already tested elsewhere
Canonical components/API contracts touched: profile page tests; merge-management page tests; linked-identity profile route tests.
