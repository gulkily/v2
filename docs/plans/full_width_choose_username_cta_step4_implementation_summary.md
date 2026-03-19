## Stage 1 - expose server-derived username CTA state
- Added [UsernameClaimCtaState](/home/wsl/v2/forum_web/profiles.py) plus `identity_can_claim_username(...)` and `resolve_username_claim_cta_state(...)` in [profiles.py](/home/wsl/v2/forum_web/profiles.py) so the server can answer username-claim eligibility per concrete signer identity while still deriving the canonical profile update route.
- Added `render_username_claim_cta_text(...)` in [api_text.py](/home/wsl/v2/forum_web/api_text.py) and the new `GET /api/get_username_claim_cta?identity_id=<identity-id>` endpoint in [web.py](/home/wsl/v2/forum_web/web.py).
- Extended the API discovery text in [api_text.py](/home/wsl/v2/forum_web/api_text.py) so the new read endpoint is advertised alongside the existing profile and merge-management reads.
- Added [test_username_claim_cta_api.py](/home/wsl/v2/tests/test_username_claim_cta_api.py) covering missing identity, unknown identity, eligible identity, spent identity, and the linked-identity case where only a peer signer has already claimed a username.

Verification:
- `python -m unittest tests.test_username_claim_cta_api tests.test_merge_management_api tests.test_profile_update_visibility`
- `python -m compileall forum_web`

## Stage 2 - render and hydrate the shared near-top CTA
- Extended the shared page shell in [templates.py](/home/wsl/v2/forum_web/templates.py) and [base.html](/home/wsl/v2/templates/base.html) so every rendered page gets one hidden near-top `Choose your username` banner mount plus the new hydration script.
- Added [username_claim_cta.js](/home/wsl/v2/templates/assets/username_claim_cta.js), which derives the current identity from the stored browser public key, requests `/api/get_username_claim_cta`, and reveals the shared banner only when the server says that signer can still claim a username.
- Added the shared CTA styling in [site.css](/home/wsl/v2/templates/assets/site.css) so the banner reads as a dedicated horizontal section near the top of the page instead of a small inline action.
- Removed the older profile-only hero CTA wiring from [web.py](/home/wsl/v2/forum_web/web.py) so the shared site-wide banner becomes the primary prompt.
- Extended [test_board_index_page.py](/home/wsl/v2/tests/test_board_index_page.py) and [test_profile_update_page.py](/home/wsl/v2/tests/test_profile_update_page.py) to assert the shared banner mount/script, and added [test_username_claim_cta_asset.py](/home/wsl/v2/tests/test_username_claim_cta_asset.py) for client hydration behavior.

Verification:
- `python -m unittest tests.test_board_index_page tests.test_profile_update_page tests.test_username_claim_cta_asset tests.test_username_claim_cta_api`
- `python -m compileall forum_web templates/assets`
