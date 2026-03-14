## Problem Statement
Choose the smallest useful way to add browser-side key generation and detached signing without turning the next loop into full identity/profile design, moderation, or a second rewrite of the posting backend.

### Option A: Add a minimal signed-posting UI inside the existing web app
- Pros:
  - Fastest path to actual frontend posting.
  - Reuses the existing renderer, template structure, and Loop 4 write contract.
  - Lets the browser generate or import an OpenPGP key, sign a canonical payload client-side, and submit it through the same posting flow the CLI already uses.
  - Produces the first end-to-end browser demo without requiring a separate client app.
- Cons:
  - Couples the first browser signing UI to the current Python-hosted web surface.
  - Requires careful boundaries so payload canonicalization, signature generation, and submission logic do not drift from the CLI contract.
  - May need later refactoring if the browser client becomes more standalone.

### Option B: Build a separate browser client page or mini-app for signing and posting
- Pros:
  - Keeps browser signing logic more isolated from the reader UI.
  - Makes it easier to treat the posting experience as a client of the CGI/API contract rather than an in-process extension.
  - May better fit a future where multiple frontends coexist.
- Cons:
  - Larger scope for the first signed-posting loop.
  - Introduces client-app structure questions before the browser posting contract is proven useful.
  - Delays the first visible frontend posting demo.

### Option C: Add detached signatures for CLI posting first, and defer browser signing
- Pros:
  - Simpler path for signature verification and canonicalization work.
  - Gives the backend a signature-aware contract before the browser touches it.
  - Useful for fixtures and parity testing.
- Cons:
  - Does not satisfy the checklist item, which is specifically about browser key generation and signed posting.
  - Leaves the frontend without posting capability for another loop.
  - Delays the first human-friendly signed-posting experience.

## Recommendation
Recommend Option A: add a minimal signed-posting UI inside the existing web app.

This is the smallest slice that gives the frontend real posting capability while building directly on Loop 4 instead of reopening the backend design. The loop should stay strict about boundaries:

- Browser code should generate or import OpenPGP keys and store them locally for now.
- The browser should sign a canonical normalized payload, not arbitrary form text.
- Signatures should be detached ASCII-armored `.asc` content, aligned with the protocol draft.
- Submission should reuse the existing posting contract rather than inventing a second write format.
- Server-side verification should be minimal and deterministic when signature policy requires it.
- Identity bootstrap, profile editing, moderation signing, and richer anonymous-mode policy should remain out of scope.

That gives the project the first true frontend posting path: a user can create or import a key in the browser, sign a thread or reply, submit it, and immediately read it back through the existing UI and API. The tradeoff is that the first browser UX stays intentionally small and utilitarian.
