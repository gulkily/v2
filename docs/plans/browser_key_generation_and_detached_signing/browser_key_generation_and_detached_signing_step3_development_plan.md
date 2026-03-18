## Stage 1
- Goal: establish the minimal browser key/signing shell and signature-aware posting helpers.
- Dependencies: approved Step 2; existing web renderer, CGI posting commands, and canonical post rules.
- Expected changes: add the smallest browser posting surface, introduce client-side helpers for canonical payload normalization, OpenPGP key generation/import, local key storage, and detached-signature creation, and extend the posting backend with signature-aware parsing, verification, and sibling `.asc` storage rules; no profile/bootstrap flow, moderation signing, or key rotation logic.
- Verification approach: open the posting UI, generate or import a key locally, sign a sample canonical payload in the browser or equivalent test harness, and confirm the backend accepts the signature-aware request shape and returns stable validation errors when required fields are missing.
- Risks or open questions:
  - letting browser-side canonicalization drift from the backend's canonical payload rules
  - introducing OpenPGP library behavior that is difficult to mirror later in non-browser or non-JavaScript implementations
- Canonical components/API contracts touched: browser-side canonical payload generation; detached signature request shape; sibling `.asc` storage and verification rules for `create_thread` and `create_reply`.

## Stage 2
- Goal: implement signed thread creation end to end from the browser.
- Dependencies: Stage 1.
- Expected changes: wire the browser posting UI to compose a root post, generate a detached signature over the canonical payload, submit both payload and signature through the existing posting contract, verify the signature server-side when policy requires it, store both the payload file and sibling `.asc` file, and return a stable success response; planned helpers such as `buildCanonicalThreadPayload(formState) -> string` and `verifyDetachedSignature(payload, signature) -> VerificationResult`.
- Verification approach: submit a signed root post from the browser, confirm a canonical payload file and `.asc` file are created, confirm a git commit is produced, and confirm the new signed thread is visible through the existing UI and read-only API.
- Risks or open questions:
  - choosing how much signature metadata, if any, is exposed in success responses or read surfaces
  - keeping the first browser UI small enough while still proving real key generation and submission
- Canonical components/API contracts touched: signed `create_thread`; detached signature verification and storage; deterministic success/error behavior for signed thread creation.

## Stage 3
- Goal: implement signed reply creation end to end from the browser.
- Dependencies: Stage 2.
- Expected changes: extend the browser posting UI to reply within an existing thread using the locally stored or imported key, sign the canonical reply payload client-side, submit payload plus detached signature, verify and store both on the backend, and preserve stable errors for invalid thread/parent targets or failed signature verification; planned helpers such as `buildCanonicalReplyPayload(formState) -> string` and `submitSignedReply(payload, signature) -> Response`.
- Verification approach: submit a signed reply from the browser to an existing thread, confirm the canonical reply file and sibling `.asc` file are created, confirm a git commit is produced, confirm the reply appears in the thread view and `get_thread`, and confirm invalid signature or invalid target cases return stable deterministic errors.
- Risks or open questions:
  - browser key persistence may need tighter UX or security policy later
  - reply verification and error reporting may need normalization for future multi-language parity fixtures
- Canonical components/API contracts touched: signed `create_reply`; reply-target validation plus detached-signature verification; deterministic signed-write success/error behavior.
