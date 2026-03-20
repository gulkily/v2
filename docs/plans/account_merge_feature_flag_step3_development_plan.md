## Stage 1
- Goal: add one shared default-off runtime flag for merge-feature availability.
- Dependencies: approved Step 2; existing environment flag helpers and config documentation patterns.
- Expected changes: introduce one canonical helper such as `merge_feature_enabled(environ: Mapping[str, str] | None = None) -> bool`; define the new env var in the same shared configuration surface used by other feature flags; thread the helper into merge-related server render paths without changing non-merge identity resolution behavior.
- Verification approach: exercise the helper with flag-on and flag-off inputs, and confirm the default state resolves to disabled.
- Risks or open questions:
  - choosing a flag name that is clearly about release visibility rather than underlying merge data
  - avoiding scattered ad hoc env checks instead of one canonical helper
- Canonical components/API contracts touched: `env_flag_enabled`; runtime configuration docs/example env; shared server-side merge availability helper.

## Stage 2
- Goal: gate merge-specific web surfaces and navigation behind the shared flag.
- Dependencies: Stage 1; existing profile page, merge pages, merge suggestion UI, and profile-nav asset behavior.
- Expected changes: suppress merge-related profile links, self-merge suggestion UI, merge-page routes, merge-action routes, and merge-targeting nav behavior when the flag is off; keep current behavior unchanged when the flag is on; planned contracts such as `render_profile_page(..., merge_feature_enabled: bool) -> str` and flag-aware merge route guards that return a missing/unavailable response instead of an active feature page.
- Verification approach: open representative profile and nav flows with the flag off and confirm merge affordances disappear; repeat with the flag on and confirm today’s merge UI returns.
- Risks or open questions:
  - making sure nav notification behavior does not still leak merge-management URLs while the feature is mothballed
  - choosing the cleanest off-state for direct merge page requests
- Canonical components/API contracts touched: `/profiles/<identity-slug>`; `/profiles/<identity-slug>/merge`; `/profiles/<identity-slug>/merge/action`; `profile_nav.js`; `profile_merge_suggestion.js`.

## Stage 3
- Goal: gate merge-specific APIs and add regression coverage for both flag states.
- Dependencies: Stage 2.
- Expected changes: make `/api/get_merge_management` and `/api/merge_request` respect the shared flag; add focused tests for profile UI, merge pages, nav behavior, and APIs in both disabled and enabled states; planned contracts such as `render_api_get_merge_management(..., merge_feature_enabled: bool)` and `render_api_merge_request(..., merge_feature_enabled: bool)`.
- Verification approach: run targeted route, asset, and API tests with the flag off and on; confirm flag-off responses do not expose the unfinished feature while flag-on responses preserve current behavior.
- Risks or open questions:
  - deciding whether disabled merge APIs should return missing-resource, unavailable-feature, or other existing response semantics
  - keeping test coverage tight enough to avoid overfitting unrelated page copy
- Canonical components/API contracts touched: `/api/get_merge_management`; `/api/merge_request`; profile/merge route tests; profile-nav asset tests; merge-specific page/API tests.
