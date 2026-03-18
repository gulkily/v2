## Problem
Signed users can currently submit their first post and trigger public-key bootstrap without any anti-abuse gate. Node operators need an optional, simple proof-of-work requirement that runs in the browser before that first signed submission is accepted.

## User Stories
- As a node operator, I want a feature flag that enables proof-of-work on signed first-post bootstrap submissions so that I can raise the cost of automated sign-up abuse.
- As a signed user, I want the browser to solve the challenge for me during compose so that I can complete my first post without manual protocol work.
- As a node operator, I want the challenge to be bound to the user's public-key fingerprint so that the work is specific to the identity being introduced.

## Core Requirements
- When the feature flag is off, signed posting and identity bootstrap behavior remain unchanged.
- When the feature flag is on, a signed user's first post/bootstrap submission must include a valid proof-of-work stamp or the request is rejected.
- The proof-of-work challenge uses a strict hash target format and is bound to the signer's public-key fingerprint.
- The gate applies to signed users as well; there is no exemption from solving the challenge for first-post bootstrap.
- Browser compose and preview/submit flows must clearly surface whether the proof-of-work requirement is pending, satisfied, or rejected.

## Shared Component Inventory
- Existing signed compose UI: reuse and extend the canonical browser signing flow for thread and reply compose because it already prepares payload, signature, and submission state.
- Existing posting APIs: extend the canonical create-thread and create-reply request contract because these already validate signed submissions and trigger identity bootstrap on first accepted signed post.
- Existing identity bootstrap behavior: reuse the current first-signed-post bootstrap path rather than creating a separate registration surface, because "registration" in this feature is the first signed post/public-key sharing event.

## Simple User Flow
1. Operator enables the proof-of-work feature flag.
2. User opens signed compose for a first post that will introduce their public key.
3. Browser derives the signed identity fingerprint, computes the proof-of-work stamp, and includes it with preview or submit.
4. Server verifies the stamp before accepting the signed first-post/bootstrap request.
5. If verification passes, the first post is accepted and normal identity bootstrap proceeds; otherwise the request is rejected with a clear error.

## Success Criteria
- With the flag off, signed first-post behavior matches current behavior.
- With the flag on, a signed first-post/bootstrap request without a valid proof-of-work stamp is rejected.
- With the flag on, a browser-composed signed first-post/bootstrap request with a valid stamp is accepted.
- Operators can enable or disable the feature with one configuration switch.
