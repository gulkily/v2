## Problem Statement
Choose the smallest useful way to make `/api/pow_requirement` return faster, without weakening the authoritative first-post PoW enforcement that still happens during signed submission.

### Option A: Add a server-side cache around public-key-to-fingerprint resolution
- Pros:
  - Preserves the current endpoint contract.
  - Keeps all fingerprint derivation on the server.
  - Helps repeated requests for the same key across one process lifetime.
- Cons:
  - Still pays the expensive derivation cost on the first request.
  - Cache effectiveness depends on process reuse and deployment shape.
  - Leaves the endpoint doing more work than needed for an advisory check.

### Option B: Let the browser send the signer fingerprint directly for `/api/pow_requirement`
- Pros:
  - Removes the expensive public-key parsing step from the hot path.
  - Fits the current browser flow, which already has local key material and can derive identity-facing data client-side.
  - Keeps the endpoint lightweight because it only needs to answer “does this fingerprint already have bootstrap state?”
  - Does not weaken final enforcement if signed post submission still verifies the real public key and signature authoritatively.
- Cons:
  - Changes the endpoint contract.
  - Requires clear rules that the endpoint is advisory and that submission-time verification remains canonical.
  - Non-browser callers would need to provide a fingerprint or keep using a slower fallback path.

### Option C: Add a persistent key-metadata index or registration-style lookup layer
- Pros:
  - Could make repeated key lookups fast across processes and across multiple endpoints.
  - Provides a broader foundation for later identity and key-management work.
- Cons:
  - Larger scope than this latency issue needs.
  - Risks reopening storage-model and synchronization questions.
  - Delays a targeted fix for one endpoint.

## Recommendation
Recommend Option B: let the browser send the signer fingerprint directly for `/api/pow_requirement`, while keeping signed submission verification authoritative on the server.

This is the smallest change that removes the current expensive step from the endpoint that users are actually waiting on. The loop should stay strict about boundaries:

- Treat `/api/pow_requirement` as an advisory preflight surface only.
- Make the endpoint answer PoW requirement questions from a fingerprint-based identity lookup instead of full public-key parsing.
- Keep `/api/create_thread` and `/api/create_reply` as the authoritative security boundary where the submitted public key and detached signature are still verified server-side.
- Leave broader key-metadata indexing, registration flows, and optimization of other signed endpoints for later work.

That gives the browser a fast preflight check without changing the real trust model for accepted signed posts.
