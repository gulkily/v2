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
