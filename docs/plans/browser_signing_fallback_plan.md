# Browser Signing Fallback Plan

## Goal

Preserve the current behavior of auto-generating or loading signing keys on page load, while ensuring that ordinary posting never fails just because browser-side signing fails.

Primary outcomes:

- User-authored content is never lost.
- `create_thread` and `create_reply` still go through even if signing is unavailable or broken.
- Unsigned fallback submissions can be reviewed or moderated later.
- Signature-required flows remain explicit about whether they can or cannot degrade gracefully.

## Current Failure Mode

The browser currently initializes OpenPGP during page load in the module entrypoints:

- `/home/wsl/v2/templates/assets/browser_signing.js`
- `/home/wsl/v2/templates/assets/merge_request_signing.js`
- `/home/wsl/v2/templates/assets/profile_nav.js`

For compose, the page also attempts to prepare keys on load. If OpenPGP fails during import or key setup, the UI shows errors such as:

- `ReferenceError: BigInt is not defined`
- `Cannot access 'Io' before initialization`

These errors come from the vendored minified OpenPGP bundle rather than from forum payload construction. For thread and reply posting, the backend already supports unsigned submissions, but the browser currently makes signing failure feel like posting failure.

## Product Constraint

Keep auto-generating or loading keys on page load.

That means the fix is not to remove eager key preparation. The fix is to make eager key preparation best-effort, well-instrumented, and non-fatal for ordinary posting.

## Design Direction

### 1. Treat signing initialization as optional capability for ordinary posts

On compose load, continue trying to:

- import OpenPGP
- load stored keys
- derive the public key if only a private key is stored
- generate a fresh keypair if needed

But if any of that fails, do not block compose or submit. Instead:

- preserve the error in structured client state
- show a clear user-facing status
- continue allowing post submission without a signature

### 2. Separate payload construction from signing

The canonical payload is the critical user artifact. Build and preserve it independently from signing so that:

- preview still works
- the exact payload can be submitted even if signing fails
- the exact payload can be retried after transient errors

### 3. Fall back to unsigned submission for ordinary posts

For `create_thread` and `create_reply`:

- attempt signed submission if signing is available
- if signing setup or signing itself fails, automatically retry as unsigned
- keep the user informed that the submission proceeded unsigned and may be subject to moderation

This aligns with existing backend behavior in `/home/wsl/v2/forum_cgi/service.py`, where `require_signature=False` by default for ordinary posts.

### 4. Preserve data until the server confirms success

Draft persistence already exists for compose text. Extend this so that the browser also preserves a pending submission snapshot until success is confirmed.

The pending snapshot should include:

- command name
- endpoint
- canonical payload
- derived post ID or record ID
- whether signed submission was attempted
- signing failure classification, if any
- timestamp of the pending attempt

Only clear this snapshot after the server accepts the submission.

## Error Handling Plan

### Client-side capability and error classification

Introduce explicit client-side classification for signing-related failures, for example:

- `insecure_context`
- `missing_bigint`
- `openpgp_import_failed`
- `stored_key_invalid`
- `public_key_derivation_failed`
- `key_generation_failed`
- `signature_creation_failed`
- `unsigned_fallback_submitted`

Keep two forms of error data:

- user-facing status text
- raw internal diagnostic text for logs or debugging

The user-facing copy should explain impact, not minified implementation details.

Example:

- user-facing: `Browser signing is unavailable here. Your post can still be submitted unsigned.`
- diagnostic: `openpgp_import_failed: Cannot access 'Io' before initialization`

### Page-load key setup behavior

On page load, preserve the current eager flow:

1. Try to initialize OpenPGP capabilities.
2. Try to load or generate local keys.
3. If successful, mark signing as available.
4. If unsuccessful, store the failure reason and mark signing as unavailable for this session.

This should update `key-status`, but must not disable compose or submission for ordinary posts.

### Submit behavior for ordinary posts

For `create_thread` and `create_reply`, submit flow should become:

1. Normalize and preserve the latest draft.
2. Build the canonical payload.
3. Persist a pending submission snapshot locally.
4. If signing is available, attempt to sign.
5. If signing succeeds, submit signed.
6. If signing fails, change status to explain fallback and submit unsigned.
7. If unsigned submit succeeds, clear pending snapshot and draft.
8. If network or server submission fails, keep pending snapshot and draft intact.

### Submit behavior for signature-required flows

Do not silently degrade all flows.

Flows that currently require signatures:

- merge requests
- profile updates
- moderation actions

These should be handled explicitly:

- either remain hard-fail with much better error messaging and preserved data
- or be redesigned later to write into a moderation or review queue when unsigned

That is a separate policy decision and should not be mixed into the ordinary-post fallback change.

## Server-side Follow-up

Unsigned ordinary posts already work. The remaining server-side improvement is to make unsigned fallback visible for moderation and later analysis.

Options:

- add a sidecar moderation intake record for unsigned fallback posts
- add a stored metadata field that records `signed=false`
- log a structured server event when a client reports unsigned fallback

Recommended minimal approach:

- keep the post record format unchanged
- add a moderation-side record or ingest path keyed by post ID for unsigned fallback submissions

This keeps canonical post storage simple while preserving reviewability.

## Implementation Steps

### Step 1. Make OpenPGP loading lazy and recoverable

In browser entrypoints, stop importing OpenPGP at module top level. Replace that with a lazy loader that:

- checks browser prerequisites
- imports OpenPGP inside `try/catch`
- caches either the loaded module or the classified failure

This avoids breaking the whole page before UI code can react.

### Step 2. Add signing availability state to compose

Track:

- `signingAvailable`
- `signingFailureCode`
- `signingFailureMessage`
- `openpgpModule`

Continue eager initialization on load, but do not tie it to overall compose viability.

### Step 3. Preserve pending submissions locally

Add a local storage entry for pending submissions separate from drafts. Drafts are editable working state; pending submissions are exact payload snapshots ready for retry.

### Step 4. Add automatic unsigned fallback for ordinary posts

If signing fails during:

- key setup
- private-to-public derivation
- signature creation

then ordinary post submission should continue without `signature` and `public_key`.

### Step 5. Improve user-visible status text

Replace raw minified bundle errors in primary UI copy with status messages that explain:

- whether data is safe
- whether posting can continue
- whether the post was submitted unsigned
- whether moderation may review it later

### Step 6. Log diagnostics cleanly

Capture raw error messages and stack traces where available, but keep them out of primary user copy. If browser logging is too noisy, add a small internal diagnostics object that can be surfaced during manual debugging.

## Acceptance Criteria

For ordinary posts:

- A user can load compose over production HTTP even if OpenPGP fails.
- The page still attempts key setup on load.
- Key setup failures do not block editing, preview, or submit.
- If signing fails, the browser retries unsigned automatically.
- Draft text is not lost.
- Pending payload is not lost if the network request fails.
- Successful unsigned submission clears pending local state.
- UI clearly communicates when fallback occurred.

For signature-required flows:

- Failures are clearly explained.
- User-entered data is preserved.
- No raw minified error is the primary UX message.

## First Implementation Slice

The smallest useful change is:

1. Make OpenPGP loading lazy in `browser_signing.js`.
2. Keep eager key setup on page load, but downgrade failures to non-blocking status.
3. Preserve pending payload before signing.
4. Retry ordinary post submission unsigned if signing fails.
5. Leave merge requests and profile updates strict for now, but improve their error reporting later.

This preserves the current product intent while making ordinary posting resilient to browser signing breakage.
