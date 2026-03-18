1. Stage 1: Define the fast fingerprint-based preflight contract
Goal: Establish one canonical `/api/pow_requirement` request/response contract that answers from a signer fingerprint instead of a full public key.
Dependencies: Approved Step 2 only.
Expected changes: Define the new request field and validation rules; add or adapt a conceptual helper such as `pow_requirement_for_fingerprint(*, repo_root: Path, signer_fingerprint: str) -> bool`; keep the response shape aligned with current browser needs.
Verification approach: Manual checks that known first-post and established-identity fingerprints produce deterministic requirement answers and that malformed fingerprint input is rejected clearly.
Risks or open questions:
- The endpoint contract should stay explicit that this is a preflight hint, not the authoritative verification boundary.
- The fingerprint format must be normalized consistently with existing identity helpers.
Canonical components/API contracts touched: `/api/pow_requirement` request contract; proof-of-work fingerprint lookup helper; current JSON response shape.

2. Stage 2: Update browser compose to use the fast preflight path
Goal: Make the browser derive and send the signer fingerprint when asking whether PoW is required.
Dependencies: Stage 1.
Expected changes: Extend the existing browser signing asset so it reuses locally available signing key data to derive the signer fingerprint before calling `/api/pow_requirement`; remove the need to send the full armored public key on that preflight path; keep existing submit behavior unchanged.
Verification approach: Manual browser smoke check that signed compose still determines PoW requirement state correctly and that the preflight request no longer depends on full public-key upload.
Risks or open questions:
- The browser should not add a second, divergent fingerprint-derivation rule.
- Existing compose state messaging must remain coherent when the preflight contract changes.
Canonical components/API contracts touched: browser signing asset; existing signed compose flow; `/api/pow_requirement` fetch contract.

3. Stage 3: Add regression coverage and preserve submission-time authority
Goal: Lock in the faster preflight behavior without weakening signed submission enforcement.
Dependencies: Stages 1-2.
Expected changes: Update endpoint tests to cover fingerprint-based preflight requests and established-identity bypass behavior; keep or extend signed submission tests to confirm `/api/create_thread` and `/api/create_reply` still require authoritative public-key/signature verification and PoW enforcement at submit time.
Verification approach: Run targeted tests plus a manual regression pass for first-post and established-identity compose flows.
Risks or open questions:
- Tests must distinguish the advisory preflight path from the authoritative submission path so later changes do not blur the boundary.
- Any fallback compatibility path for older callers should remain deterministic if included.
Canonical components/API contracts touched: `/api/pow_requirement` tests; signed submission tests for create-thread/create-reply; browser preflight behavior under first-post PoW.
