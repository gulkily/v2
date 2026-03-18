1. Stage 1: Define PoW policy and first-post detection boundary
Goal: Add one canonical policy surface for the feature flag and the first-signed-post/bootstrap check.
Dependencies: Approved Step 2 only.
Expected changes: Add env/config readers for a single enable flag and fixed difficulty; add a conceptual helper such as `pow_required_for_signed_post(*, repo_root: Path, signer_fingerprint: str) -> bool` that reuses existing identity bootstrap state.
Verification approach: Manual check that config defaults leave current behavior unchanged and that known existing identities are not treated as first-post bootstrap.
Risks or open questions:
- Assumption: the gate applies only when the signer does not already have an identity bootstrap record.
- Assumption: fingerprint-bound first-post detection is sufficient for v1.
Canonical components/API contracts touched: existing repo env loading, current signed posting/identity bootstrap service contract.

2. Stage 2: Add canonical PoW verification to signed posting APIs
Goal: Extend signed create-thread/create-reply submissions to accept and verify a PoW stamp when required.
Dependencies: Stage 1.
Expected changes: Extend the JSON request contract with PoW fields; add a conceptual verifier such as `verify_pow_stamp(*, public_key_text: str, payload_text: str, stamp: str) -> None`; thread the result through `render_api_create_thread`, `render_api_create_reply`, and `submit_create_thread`/`submit_create_reply`.
Verification approach: Manual API smoke checks for flag off, missing stamp, invalid stamp, and valid stamp on a first signed post.
Risks or open questions:
- Assumption: bind the stamp to signer fingerprint plus exact `Post-ID` to narrow replay without adding challenge state.
- Assumption: dry-run preview also requires valid PoW when the gate is active so preview and final submit share one acceptance rule.
Canonical components/API contracts touched: create-thread/create-reply JSON request contract and canonical submission result/error flow.

3. Stage 3: Extend browser signing compose flow to compute and submit PoW
Goal: Make signed compose automatically derive the PoW stamp before preview/submit.
Dependencies: Stage 2.
Expected changes: Extend `browser_signing.js` state and submit path with deterministic hash computation, PoW status messaging, and request fields; extend compose template messaging only through existing status surfaces.
Verification approach: Manual browser smoke check that first-post compose shows solving/progress, sends PoW on preview/submit, and leaves later signed posts unchanged when PoW is not required.
Risks or open questions:
- Browser solve time may need user-visible status for higher difficulty values.
- Non-browser clients remain unsupported in this feature.
Canonical components/API contracts touched: existing signed compose page, browser signing asset, create-thread/create-reply request payload shape.

4. Stage 4: Cover failure modes and operator-facing defaults
Goal: Finalize clear rejection behavior, docs-adjacent config defaults, and regression coverage for the signed first-post path.
Dependencies: Stages 1-3.
Expected changes: Add/extend targeted tests around first-post detection and PoW verification; add the new env default to `.env.example`; ensure server errors remain canonical and human-readable.
Verification approach: Run targeted tests plus a manual regression check for normal signed posting with the flag disabled.
Risks or open questions:
- If first-post detection has edge cases around partially written identity artifacts, they must fail closed without blocking established identities incorrectly.
- Difficulty must stay low enough for browser UX in v1.
Canonical components/API contracts touched: env default surface, signed posting error contract, test coverage for CGI/web posting flow.
