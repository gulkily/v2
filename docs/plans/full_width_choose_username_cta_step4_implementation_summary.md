## Stage 1 - expose server-derived username CTA state
- Added [UsernameClaimCtaState](/home/wsl/v2/forum_web/profiles.py) plus `identity_can_claim_username(...)` and `resolve_username_claim_cta_state(...)` in [profiles.py](/home/wsl/v2/forum_web/profiles.py) so the server can answer username-claim eligibility per concrete signer identity while still deriving the canonical profile update route.
- Added `render_username_claim_cta_text(...)` in [api_text.py](/home/wsl/v2/forum_web/api_text.py) and the new `GET /api/get_username_claim_cta?identity_id=<identity-id>` endpoint in [web.py](/home/wsl/v2/forum_web/web.py).
- Extended the API discovery text in [api_text.py](/home/wsl/v2/forum_web/api_text.py) so the new read endpoint is advertised alongside the existing profile and merge-management reads.
- Added [test_username_claim_cta_api.py](/home/wsl/v2/tests/test_username_claim_cta_api.py) covering missing identity, unknown identity, eligible identity, spent identity, and the linked-identity case where only a peer signer has already claimed a username.

Verification:
- `python -m unittest tests.test_username_claim_cta_api tests.test_merge_management_api tests.test_profile_update_visibility`
- `python -m compileall forum_web`
