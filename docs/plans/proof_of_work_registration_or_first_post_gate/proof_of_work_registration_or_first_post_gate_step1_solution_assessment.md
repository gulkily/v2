## Problem Statement
Choose the smallest robust way to require a proof-of-work challenge before a signed user's first post/public-key bootstrap without adding a heavyweight anti-abuse system.

### Option A: Browser-only Hashcash-style stamp embedded in the submitted payload
- Pros:
  - Keeps the solve step in the existing web frontend JavaScript flow.
  - Fits the current CGI-style submission model with minimal new moving parts.
  - Can bind the challenge to the signer's public-key fingerprint so the work is specific to the identity being introduced.
  - Matches the desired scope: signed users, first post/bootstrap moment, one feature flag, and no non-browser path in v1.
- Cons:
  - Replay still needs server-side rules, such as storing used stamps or binding the stamp to the exact post context.
  - Easier to precompute if the fingerprint-bound input is too stable across attempts.
  - Gives the operator less control over per-request freshness than a server-issued nonce.

### Option B: Server-issued nonce challenge solved in browser JavaScript and verified on submit
- Pros:
  - Gives the node a clear place to set difficulty, expiry, and scope per action.
  - Reduces replay risk because the challenge can be one-time, short-lived, and bound to first-post/bootstrap context.
  - Works cleanly with the existing submit/preview pattern by adding challenge fields to the request contract.
- Cons:
  - Adds a challenge issuance surface and short-term state or signed challenge tokens.
  - Larger feature than a pure fingerprint-bound client-side stamp.
  - Solves a broader problem than the current v1 scope needs.

### Option C: CAPTCHA or external anti-bot service
- Pros:
  - Familiar operator model and potentially stronger commodity bot resistance.
  - Offloads puzzle design and tuning.
- Cons:
  - Conflicts with the project's preference for simple local primitives and browser-generated request data.
  - Adds third-party dependency or more complex UX/accessibility tradeoffs.
  - Does not align with the desired hash-computation approach.

## Recommendation
Selected direction: Option A, a browser-computed Hashcash-style stamp verified on submit and bound to the signer's public-key fingerprint.

This matches the narrowed scope better: the gate is always required when the user introduces a signed identity through their first post/bootstrap path, runs entirely in the existing browser JavaScript compose flow, and is controlled by a single feature flag. The main caveat is replay resistance, so Step 2 should make the stamp input and server-side acceptance rules explicit enough that a fingerprint-bound stamp cannot be reused too broadly.
