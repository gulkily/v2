## Stage 1
- Goal: Define one canonical compose-status presentation path that can make active proof-of-work work visually prominent near the primary action area.
- Dependencies: Approved Step 2; existing compose template in `templates/compose.html`; existing shared status styling in `templates/assets/site.css`.
- Expected changes: conceptually reposition or wrap the current submit-status surface so it lives with the main action area instead of reading like a footer note; add a small shared styling contract for idle versus active status states without introducing a separate modal or overlay component.
- Verification approach: manual browser smoke check that the compose page shows the status surface in the main action area before any submission starts and that idle presentation remains unobtrusive.
- Risks or open questions:
  - Need the active treatment to stand out without making routine idle copy visually noisy.
  - Need to preserve the existing page structure for thread and reply compose rather than creating command-specific variants.
- Canonical components/API contracts touched: `templates/compose.html`; shared compose/status styles in `templates/assets/site.css`.

## Stage 2
- Goal: Thread proof-of-work solving through the canonical browser signing status flow so active waiting states trigger the stronger presentation and later phases return to normal status treatment.
- Dependencies: Stage 1; existing compose submit flow and PoW progress updates in `templates/assets/browser_signing.js`.
- Expected changes: conceptually extend the existing status update helper surface with a lightweight notion of status emphasis or phase, and use it for proof-of-work lookup/solve, signing, submit, success, and failure messages; planned signature updates may include evolving `setStatus(id, message)` into a status helper that can also set a state token for styling or semantics.
- Verification approach: manual smoke check for a signed compose that requires proof-of-work, confirming the waiting message becomes prominent during solve, updates during attempt progress, and then transitions cleanly into signing/submission/success or failure states.
- Risks or open questions:
  - Need to keep one shared status contract so other compose states do not drift into ad hoc styling.
  - Need to decide whether signing and submit should share the same active emphasis as proof-of-work or use a milder state.
- Canonical components/API contracts touched: `templates/assets/browser_signing.js`; existing compose DOM ids and submission-state messaging contract.

## Stage 3
- Goal: Add focused regression coverage for the new compose-status presentation so the active PoW wait remains visible in the canonical signed compose flow.
- Dependencies: Stages 1-2; existing compose and web test surfaces.
- Expected changes: extend targeted rendering or route tests to assert that the compose page exposes the canonical action-area status surface, and add focused browser-signing behavior coverage where practical for active proof-of-work state transitions without introducing a new end-to-end framework.
- Verification approach: run the relevant targeted tests for compose rendering and any browser-signing coverage that exists, plus one final manual browser smoke check of the full PoW-required submission flow.
- Risks or open questions:
  - Frontend behavioral coverage may be limited if browser-signing tests are currently thin.
  - Need assertions that are stable around semantics and structure rather than brittle exact copy.
- Canonical components/API contracts touched: compose rendering tests, any existing browser-signing test surface, and the canonical signed compose route/template contract.
