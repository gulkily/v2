1. Goal: expose one shared “show initial username claim callout” signal from the existing profile eligibility state.
Dependencies: approved Step 2; current repository-state username-update eligibility helper used by profile read surfaces.
Expected changes: add one narrow helper or page-context field such as `ProfileSummary.show_username_claim_callout: bool` or `profile_should_show_username_claim_callout(summary, identity_context) -> bool`; derive it directly from the existing eligibility rule so the callout appears only for profiles that can still update their username.
Verification approach: build/read fixtures for eligible and ineligible profiles and confirm the derived callout signal follows the current eligibility rule exactly.
Risks or open questions:
- the callout signal must not drift from the action-link eligibility rule
- the feature should not introduce a second interpretation of eligibility separate from the backend/write model
Canonical components/API contracts touched: shared profile read helper/context; profile page rendering inputs.

2. Goal: render a clear username-claim callout in the profile page header/hero for eligible profiles only.
Dependencies: Stage 1; existing `/profiles/<identity-slug>` page hero/header and action cluster.
Expected changes: extend the profile page rendering path so eligible profiles show a concise header-level callout with a link to `/profiles/<identity-slug>/update`; keep the hero clean for ineligible profiles and do not add a new page or new write flow.
Verification approach: manually render eligible and ineligible profile pages and confirm the callout appears only for eligible cases, with the existing update flow as its target.
Risks or open questions:
- the added callout should improve discoverability without making the hero feel crowded
- the new prominent affordance should not conflict visually with the existing action cluster
Canonical components/API contracts touched: `render_profile_page(...)`; profile page template and hero content; existing `/profiles/<identity-slug>/update` route.

3. Goal: lock in regression coverage for visible and hidden header callouts.
Dependencies: Stages 1-2; existing profile-page tests for username-update visibility.
Expected changes: add focused tests proving that eligible profiles show the prominent callout, ineligible profiles hide it, and the callout continues to point at the existing update route rather than a new surface.
Verification approach: run targeted profile-page tests with fixtures covering both no-claim and already-claimed profiles.
Risks or open questions:
- tests should assert the new prominent header copy without becoming brittle about unrelated hero text
- coverage should complement, not duplicate, the recent affordance-hiding tests
Canonical components/API contracts touched: profile page tests; profile rendering copy for the eligible-callout state.
