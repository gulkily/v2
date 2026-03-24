## Stage 1 - Add a server-signed identity-hint cookie contract
- Changes:
  - Added `forum_web/identity_hint.py` with fingerprint normalization, HMAC-signed cookie creation, validation, and clear-cookie helpers.
  - Added `POST /api/set_identity_hint` so the browser can set or clear the signed identity-hint cookie through the server.
  - Added `.env.example` documentation for `FORUM_IDENTITY_HINT_SECRET`.
- Verification:
  - `python -m unittest tests.test_identity_hint tests.test_identity_hint_api`
- Notes:
  - The hint cookie is scoped as personalization state only; it is not treated as authentication.

## Stage 2 - Feed the shared account-setup banner from validated hint-cookie state
- Changes:
  - Added per-request banner-state propagation through the shared page shell so `render_page(...)` can render the `Account setup` module visibly when a validated hint cookie resolves to an eligible identity.
  - Updated the shared banner renderer to populate the initial CTA href in server HTML while keeping hidden fallback behavior for missing or invalid hint state.
  - Added request-level regression coverage for board-index and compose-page initial render behavior with valid and invalid hint cookies.
- Verification:
  - `python -m unittest tests.test_account_setup_initial_render tests.test_board_index_page tests.test_compose_thread_page`
- Notes:
  - Existing `tests.test_profile_update_page` failures around the profile action link remain outside this slice and were not introduced by the shared-banner change.

## Stage 3 - Update browser enhancement code to maintain the hint cookie and refresh banner state
- Changes:
  - Updated `templates/assets/username_claim_cta.js` to derive the active fingerprint from the stored key, sync the signed hint cookie through `/api/set_identity_hint`, and then refresh CTA state from the existing eligibility endpoint.
  - Kept the banner hidden when the local key is absent or refresh resolves ineligible, while avoiding the previous eager hide-before-refresh behavior for the normal eligible case.
  - Extended CTA asset coverage to verify fingerprint extraction, hint-cookie sync requests, and no-key fallback behavior.
- Verification:
  - `python -m unittest tests.test_username_claim_cta_asset tests.test_account_setup_initial_render`
- Notes:
  - The browser still treats the hint cookie as synchronization state only; privileged actions continue using signed request flows.

## Stage 4 - Add focused regression coverage for cookie validation, initial HTML, and enhancement boundaries
- Changes:
  - Added stale-cookie page coverage so expired hint cookies fail closed to the hidden banner state in initial HTML.
  - Ran the focused end-to-end regression suite covering cookie signing, cookie sync, SSR banner rendering, and representative shared pages.
- Verification:
  - `python -m unittest tests.test_identity_hint tests.test_identity_hint_api tests.test_account_setup_initial_render tests.test_username_claim_cta_asset tests.test_board_index_page tests.test_compose_thread_page`
- Notes:
  - The focused suite passed.
