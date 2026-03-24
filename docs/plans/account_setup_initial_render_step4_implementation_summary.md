## Stage 1 - Add a server-signed identity-hint cookie contract
- Changes:
  - Added `forum_web/identity_hint.py` with fingerprint normalization, HMAC-signed cookie creation, validation, and clear-cookie helpers.
  - Added `POST /api/set_identity_hint` so the browser can set or clear the signed identity-hint cookie through the server.
  - Added `.env.example` documentation for `FORUM_IDENTITY_HINT_SECRET`.
- Verification:
  - `python -m unittest tests.test_identity_hint tests.test_identity_hint_api`
- Notes:
  - The hint cookie is scoped as personalization state only; it is not treated as authentication.
