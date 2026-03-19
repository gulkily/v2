## Stage 1
- Goal: expose one server-derived identity-scoped username-claim CTA state payload.
- Dependencies: approved Step 2; existing username-claim eligibility rule; existing profile/update target resolution helpers; existing text API patterns.
- Expected changes: add one narrow server helper and read contract that accepts an `identity_id` and returns whether that signer identity can still claim a username plus the existing update target to use when eligible; reuse the current one-claim-per-signer rule and `/profiles/<identity-slug>/update` route instead of inventing new eligibility semantics; planned contracts such as `resolve_username_claim_cta_state(identity_id, identity_context, posts) -> UsernameClaimCtaState | None` and an endpoint/result shape including `identity_id`, `can_claim_username`, and `update_href`.
- Verification approach: exercise the helper and endpoint with fixtures covering unknown identity, eligible identity, and spent/ineligible identity; confirm the payload stays aligned with current repository-state eligibility and produces the existing update route only for eligible identities.
- Risks or open questions:
  - keeping the payload minimal so it exposes only CTA state, not a broader account/session surface
  - ensuring the server remains the sole source of truth for “has this identity already claimed a username?”
- Canonical components/API contracts touched: identity-scoped CTA-state helper; read endpoint or API response contract; canonical `/profiles/<identity-slug>/update` route target.

## Stage 2
- Goal: derive the current browser-key identity on the client and hydrate a shared near-top `Choose your username` CTA section from the Stage 1 payload.
- Dependencies: Stage 1; existing browser-stored key handling in frontend assets; existing shared page shell in `forum_web/templates.py`; existing page renderers that flow through the shared layout.
- Expected changes: extend the shared layout so it includes one hidden dedicated horizontal CTA section near the top of normal pages, add client-side logic that derives the current identity from the stored public key, requests the server CTA-state payload for that identity, and reveals the CTA only when `can_claim_username` is true; remove or supersede the older profile-only hero CTA so the shared site-wide CTA is the primary prompt.
- Verification approach: manually load representative pages with no stored key, an eligible stored key, and a spent/ineligible stored key; confirm the CTA stays hidden in the first and third cases, appears near the top in the eligible case, and links to the existing update page.
- Risks or open questions:
  - deciding which pages count as “normal pages” for this slice without dragging in special-purpose or form-specific layouts unnecessarily
  - keeping the client logic limited to identity derivation and CTA hydration rather than duplicating server-side eligibility rules
- Canonical components/API contracts touched: shared page shell/header contract; frontend browser-key asset; identity-to-CTA-state fetch contract.

## Stage 3
- Goal: add regression coverage for server CTA-state derivation plus client-visible CTA rendering and suppression across page types.
- Dependencies: Stages 1-2.
- Expected changes: add focused tests proving the server returns the correct eligibility payload per identity, that representative shared-layout pages expose the hidden CTA mount point, and that the client asset reveals or suppresses the CTA correctly for eligible, ineligible, and no-key contexts while preserving the existing update-route target.
- Verification approach: run targeted server tests for the CTA-state contract, targeted page tests for the shared near-top section, and targeted asset tests for client hydration behavior.
- Risks or open questions:
  - avoiding brittle layout assertions while still proving the CTA is a shared page-level affordance
  - keeping the asset tests narrow so they validate behavior without mirroring full browser integration
- Canonical components/API contracts touched: CTA-state helper/endpoint tests; shared page/layout tests; frontend asset tests for CTA hydration.
