## Problem
`/api/pow_requirement` currently does more work than necessary for a browser preflight check because it derives a fingerprint from the full armored public key on every request. The next slice should make that endpoint fast enough for interactive compose flows by letting it answer from a signer fingerprint, while keeping signed submission verification unchanged and authoritative.

## User Stories
- As a signed browser user, I want `/api/pow_requirement` to return quickly so that compose can decide whether proof-of-work is needed without a noticeable delay.
- As a node operator, I want the preflight speedup to avoid weakening the real first-post PoW gate so that accepted signed posts still go through full server-side verification.
- As a future backend implementer, I want the preflight contract to be explicit and deterministic so that other implementations can reproduce the same fast-path behavior.

## Core Requirements
- The slice must make `/api/pow_requirement` answer from a signer fingerprint rather than requiring full public-key parsing on the hot path.
- The slice must keep `/api/create_thread` and `/api/create_reply` as the authoritative enforcement boundary where the submitted public key and detached signature are still verified server-side.
- The slice must preserve the current PoW decision rule: PoW is required only when the signer fingerprint does not already have visible bootstrap state and the feature flag is enabled.
- The slice must keep the browser compose flow coherent by reusing the existing signing/key-management client logic rather than adding a separate key-registration UX.
- The slice must avoid broader key-metadata indexing, registration flows, or optimization of unrelated signed endpoints.

## Shared Component Inventory
- Existing browser compose/signing flow: reuse and extend the canonical browser signing asset because it already has local access to the user's signing key and currently calls `/api/pow_requirement`.
- Existing PoW preflight API: extend `/api/pow_requirement` because it is already the browser-facing surface for first-post PoW state.
- Existing signed write APIs: reuse `/api/create_thread` and `/api/create_reply` unchanged as the canonical security boundary for signature verification and PoW enforcement.
- Existing identity bootstrap lookup: reuse the current bootstrap-state rule based on signer fingerprint rather than introducing a new identity or registration surface.

## Simple User Flow
1. User opens signed compose in the browser.
2. Browser derives the signer fingerprint from the locally available signing key material.
3. Browser calls `/api/pow_requirement` with that fingerprint.
4. Server checks whether first-post PoW is required for that fingerprint and returns the requirement state plus configured difficulty.
5. Browser either solves PoW or skips it, then submits the signed post through the existing signed write endpoint.
6. Server performs the normal authoritative signature verification and PoW enforcement during submission.

## Success Criteria
- `/api/pow_requirement` no longer needs the full armored public key to answer the browser preflight request.
- Browser signed compose can determine PoW requirement state using the new fast preflight contract.
- Accepted signed posts still require the current authoritative server-side signature verification and first-post PoW enforcement behavior.
- The returned `required`, `difficulty`, and signer identity information remain deterministic for a given fingerprint and repository state.
