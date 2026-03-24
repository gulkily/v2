1. Stage 1: Add a server-signed identity-hint cookie contract
Goal: create the request-time identity mechanism that lets the browser tell the server which fingerprint to use for SSR personalization without introducing an auth/session system.
Dependencies: Approved Step 2; existing browser key/fingerprint derivation in `profile_nav.js`; current web request handling in `forum_web/web.py`.
Expected changes: add a small endpoint or shared request path that accepts the browser-derived fingerprint and returns a server-set cookie containing the fingerprint plus expiry/version and an HMAC-style signature with a server-only secret; define clear invalidation behavior when the local key disappears or changes; planned contracts such as `set_identity_hint_cookie(...)`, `read_identity_hint_cookie(...)`, and `clear_identity_hint_cookie(...)` only if needed; no database changes.
Verification approach: exercise cookie set/read/clear flows and confirm valid cookies round-trip, tampered cookies fail validation, and missing cookies fall back safely.
Risks/Open questions:
- Keep the cookie explicitly scoped as a rendering hint, not an authorization primitive.
- Avoid exposing more than the fingerprint or relying on reversible client-stored secrets.
Canonical components/API contracts touched: browser fingerprint derivation path; new identity-hint cookie contract; web request/cookie handling.

2. Stage 2: Feed the shared account-setup banner from validated hint-cookie state
Goal: make the shared page shell capable of rendering the `Account setup` banner in visible or hidden form from validated request-time identity-hint state.
Dependencies: Stage 1; existing shared banner rendering in `forum_web/templates.py`; existing username-claim state resolver in `forum_web/profiles.py` / `forum_web/web.py`.
Expected changes: introduce a shared banner-state input for `render_page(...)` / `render_username_claim_cta_html()` and a shared helper that validates the hint cookie, resolves eligibility through the existing canonical claim logic, and supplies the correct update href when eligible; keep placement, copy, and destination unchanged; no database changes.
Verification approach: render representative pages with valid eligible, valid ineligible, missing, and invalid hint-cookie states and confirm the initial HTML matches the resolved banner state.
Risks/Open questions:
- Keep eligibility logic sourced from the existing canonical resolver rather than duplicating claim rules in templates.
- Ensure invalid or stale cookies fail closed and do not produce a false-positive banner.
Canonical components/API contracts touched: shared page shell; shared `Account setup` banner renderer; username-claim eligibility resolver; new identity-hint cookie contract.

3. Stage 3: Update browser enhancement code to maintain the hint cookie and refresh banner state
Goal: preserve browser-driven correctness while shifting first-render visibility to the server for requests carrying a valid identity hint.
Dependencies: Stages 1-2; existing assets `templates/assets/profile_nav.js` and `templates/assets/username_claim_cta.js`; existing API `/api/get_username_claim_cta`.
Expected changes: update the browser path so it derives the current fingerprint from the stored key, keeps the hint cookie synchronized through the new server endpoint, and continues refreshing banner href/visibility when browser context changes; keep the CTA asset as an enhancement/correction layer rather than the primary first-reveal mechanism.
Verification approach: exercise browser flows for first hint registration, key change, key removal, eligible refresh, and ineligible refresh, confirming the banner and cookie move together coherently.
Risks/Open questions:
- Avoid repeated background writes when the derived fingerprint has not changed.
- Keep client refresh behavior from fighting correct server-rendered markup or leaving stale hint cookies behind.
Canonical components/API contracts touched: `profile_nav.js`; `username_claim_cta.js`; new hint-cookie sync endpoint; `/api/get_username_claim_cta`.

4. Stage 4: Add focused regression coverage for cookie validation, initial HTML, and enhancement boundaries
Goal: lock in the new contract that a valid server-signed hint cookie enables correct initial HTML while invalid cookies fail closed and client code remains secondary enhancement.
Dependencies: Stages 1-3.
Expected changes: extend request/page tests for valid, invalid, stale, and missing hint-cookie cases; add coverage for cookie signing/validation helpers and the sync endpoint; update CTA asset tests to cover pre-rendered visible/hidden states plus cookie-maintenance behavior; no new production surfaces.
Verification approach: run focused Python request/page tests and Node asset tests covering cookie integrity, server-visible eligible output, server-hidden fallback cases, and client refresh/sync behavior.
Risks/Open questions:
- Avoid brittle tests tied to incidental header formatting or exact markup order outside the shared banner contract.
- Keep the test matrix representative without turning the feature into a broader session-system test suite.
Canonical components/API contracts touched: cookie signing/validation helpers; sync endpoint tests; shared page rendering tests; username-claim CTA asset tests.
