# Submission Process Rubber-Duck Review

Purpose: review the end-to-end browser submission flow for thread/reply posting, identify brittle points, and recommend hardening work so ordinary posting survives partial browser-signing failure.

Date: 2026-03-18

## Execution Reminder

Reminder to self: commit after each addressed hardening step, then check off the matching item below in the same commit.

## Execution Checklist

- [x] Step 1: make signing-status text and submit-mode copy deterministic
- [x] Step 2: add reply-path parity tests for unsigned-fallback flag off/on
- [x] Step 3: add a visible clear-saved-submission control
- [ ] Step 4: stop treating dry-run previews as pending publish attempts

## Scope

Reviewed paths:

- [browser_signing.js](/home/wsl/v2/templates/assets/browser_signing.js)
- [openpgp_loader.js](/home/wsl/v2/templates/assets/openpgp_loader.js)
- [compose.html](/home/wsl/v2/templates/compose.html)
- [web.py](/home/wsl/v2/forum_web/web.py)
- [service.py](/home/wsl/v2/forum_cgi/service.py)

This review focuses on ordinary post submission:

- `create_thread`
- `create_reply`

It also notes a few implications for:

- profile updates
- merge requests

## Current Flow

For ordinary compose pages, the browser currently does this:

1. Render the compose page with server-provided data attributes.
2. Attach the submit handler in `browser_signing.js`.
3. Try background signing setup:
   - load OpenPGP
   - load or generate local keys
   - derive public key
4. Build the canonical payload in the browser.
5. On submit:
   - normalize body text
   - rebuild canonical payload
   - optionally compute proof-of-work
   - try to sign
   - submit signed, or unsigned if fallback is enabled and signing failed
6. Store local draft and pending-submission state in `localStorage`.
7. Clear local state only after server success.

Server-side, the write endpoint does this:

1. Parse JSON request.
2. Read `payload`, optional `signature`, and optional `public_key`.
3. Decide whether signature is required.
4. Validate signature if present.
5. Validate payload structure.
6. Write records and return a response payload.

## Main Findings

### 1. Frontend capability and backend policy can drift apart

This was the immediate source of the user-visible error:

- the browser believed ordinary posting could continue unsigned
- the backend still required `signature` and `public_key`

This is better now that `FORUM_ENABLE_UNSIGNED_POST_FALLBACK` drives both sides, but the system is still vulnerable to drift whenever:

- UI copy is changed separately from server policy
- new endpoints are added and do not reuse the same gate
- one page forgets to emit the controlling data attribute

Risk:

- user sees “posting can continue unsigned”
- server rejects the request anyway

Hardening direction:

- keep one source of truth for ordinary-post signature policy
- make the page render explicit about the active mode
- add regression coverage for flag off and flag on for both thread and reply flows

### 2. Local pending-submission state is sticky and user-facing copy is vague

The current browser shows:

- `A previous submission attempt is still saved locally from ...`

That is technically true, but operationally weak:

- it does not say whether the saved attempt was signed or unsigned
- it does not say whether the browser will retry automatically
- it does not expose a “clear it” action
- it does not distinguish dry-run preview from real post attempt

Risk:

- users think the app is wedged
- stale local state survives longer than intended
- support/debugging becomes guesswork

Hardening direction:

- record more structured pending-submission metadata
- show whether the pending snapshot came from:
  - signed attempt
  - unsigned fallback attempt
  - dry run
  - server/network failure
- add a visible “clear saved submission” button

### 3. Signing-status messaging is still easy to misstate

The user’s exact report exposed this class of brittleness:

- signing capability message
- submit-mode message
- backend acceptance policy

These must stay aligned, but today they are assembled in multiple places:

- `formatSigningStatus`
- fallback submit messaging
- initial status text in templates
- server configuration

Risk:

- misleading or contradictory UX
- support burden from messages that are individually reasonable but jointly false

Hardening direction:

- separate these message concepts explicitly:
  - signing available or unavailable
  - unsigned fallback allowed or not allowed
  - current submit mode for this page
- avoid message text that implies a fallback path unless it is actually enabled

### 4. The compose path depends heavily on local browser features

Current ordinary posting depends on:

- `BigInt`
- `crypto.getRandomValues`
- secure-context behavior for module crypto usage
- `localStorage`
- module loading for `openpgp_loader.js`

The system now degrades better than before, but the compose surface is still browser-fragile.

Risk:

- older browsers fail in multiple independent ways
- failure mode differs by feature combination
- testing only modern browsers misses real-world breakage

Hardening direction:

- create an explicit “browser capability matrix” for compose
- test at least these degraded cases:
  - no `BigInt`
  - no OpenPGP import
  - no `localStorage`
  - no secure context
  - no signing but unsigned fallback on
  - no signing and unsigned fallback off

### 5. Ordinary posting still uses one large client flow

`browser_signing.js` currently owns:

- normalization
- draft persistence
- pending-submission persistence
- signing setup
- proof-of-work lookup and solving
- submission transport
- redirect behavior

This is workable, but brittle because unrelated concerns can interfere with each other.

Risk:

- fixing one path breaks another
- status text becomes overloaded
- state transitions are hard to reason about

Hardening direction:

- split the client flow conceptually into:
  - payload building
  - signing capability
  - submission transport
  - local recovery state
- even if it remains one file for now, the state machine should be made more explicit

### 6. Reply flow needs the same explicit coverage as thread flow

The backend flag now applies to both thread and reply endpoints, which is good.

What is still missing from the current confidence level:

- explicit reply-page render tests for the unsigned-fallback flag
- explicit reply-endpoint tests for flag off/on unsigned behavior

Risk:

- thread path works
- reply path drifts later

Hardening direction:

- add mirrored coverage for reply compose and reply submit

### 7. Dry-run preview and real submit are not cleanly separated in local persistence

The browser stores pending-submission data even though dry-run preview is not a real publish attempt.

Risk:

- local “pending submission” state may reflect preview activity
- user-facing recovery state becomes noisy or misleading

Hardening direction:

- either do not store pending submission for dry runs
- or store it under a separate preview-only key and never show it as a publish attempt

### 8. Signature-required flows are still harder than ordinary posting

This is not necessarily wrong, but it is a product sharp edge.

For:

- profile updates
- merge requests

current behavior is still:

- signing must work
- otherwise the action fails

That is acceptable for now, but the UX should be intentionally strict rather than incidentally strict.

Hardening direction:

- give these pages explicit copy:
  - “This action requires signing”
  - “Unsigned fallback is not available here”
- preserve user-entered data robustly on failure

## Exact User-Reported Issue

The reported frontend sequence was:

1. stale saved-submission notice
2. browser-signing-unavailable notice
3. signed-posting failure from server requiring signature

Root cause:

- the browser UI and the backend signature requirement were not consistently gated by the same feature decision

Secondary issue:

- the saved-pending-submission notice amplified confusion because it suggested residual broken state without clarifying what was saved or why

## Recommended Hardening Priorities

### Priority 1: make state and messaging deterministic

- ensure unsigned-fallback messaging is only shown when the flag is actually on
- show current effective submit mode explicitly:
  - signed
  - unsigned fallback allowed
  - signature required

### Priority 2: make recovery state user-actionable

- add “clear saved submission”
- add “retry using current payload”
- identify whether saved submission is:
  - signed attempt
  - unsigned attempt
  - preview only

### Priority 3: add reply-path parity tests

- reply compose page emits the flag
- reply endpoint rejects unsigned when flag is off
- reply endpoint accepts unsigned when flag is on

### Priority 4: separate dry run from publish in local state

- do not reuse the same pending-submission UX for both

### Priority 5: tighten signature-required pages

- clearer copy on profile-update and merge-request pages
- better distinction between:
  - signing unavailable
  - wrong key loaded
  - signature required by policy

## Minimal “Less Brittle” Target

The minimum robust behavior for ordinary posting should be:

- compose page loads even when OpenPGP is unusable
- submit handler always attaches
- user can always build canonical payload
- if unsigned fallback is off:
  - UI says signing is required
  - button copy does not imply fallback
  - server rejects unsigned consistently
- if unsigned fallback is on:
  - UI says unsigned fallback is allowed
  - browser retries unsigned automatically
  - server accepts unsigned consistently
- stale local pending state can be cleared explicitly

## Suggested Next Implementation Slice

If continuing this work, the next slice should be:

1. fix signing-status text so it reflects the unsigned-fallback flag
2. add reply-path flag and unsigned-submit tests
3. add a visible “clear saved submission” control
4. stop treating dry-run previews as pending publish attempts

That would reduce confusion more than adding deeper browser-signing sophistication first.
