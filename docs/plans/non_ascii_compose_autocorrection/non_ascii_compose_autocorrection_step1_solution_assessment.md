## Problem Statement
Choose the smallest useful way to automatically correct non-ASCII characters in a user's composed message without breaking the existing signed canonical payload and ASCII-only storage rules.

### Option A: Add deterministic browser-side correction before payload signing
- Pros:
  - Fits the current compose flow, where the browser already builds the canonical payload preview and detached signature.
  - Keeps the signed payload, stored record, and user-visible preview aligned because correction happens before signing.
  - Preserves the backend's current ASCII-only contract instead of adding silent server mutations.
  - Can give the user immediate readback of the corrected text in the compose UI.
- Cons:
  - Requires choosing a narrow, predictable correction policy for characters like smart quotes, dashes, and ellipses.
  - May surprise users if the browser rewrites text without clear visibility.
  - Needs shared handling across thread, reply, and other browser-signed compose surfaces.

### Option B: Add server-side correction during submission
- Pros:
  - Centralizes correction logic in one backend path.
  - Covers non-browser clients that submit invalid text.
  - Keeps the browser UI simpler in the short term.
- Cons:
  - Conflicts with the current signing model because mutating the payload after the browser signs it breaks signature integrity.
  - Makes the stored record differ from the user's signed preview unless the signing contract is redesigned.
  - Pushes the loop toward rewriting canonicalization rules instead of adding a small UX improvement.

### Option C: Keep rejection behavior but add browser warnings and one-click manual replacement
- Pros:
  - Lowest correctness risk because the browser never silently rewrites text.
  - Keeps the existing ASCII-only contract fully explicit.
  - Easier to explain because the user approves each correction.
- Cons:
  - Does not actually satisfy the request for automatic correction.
  - Leaves extra friction in the compose flow.
  - Still requires users to do cleanup work when the browser could handle obvious substitutions.

## Recommendation
Recommend Option A: add deterministic browser-side correction before payload signing.

This is the smallest coherent solution because the current product already derives and signs the canonical payload in the browser, while the backend expects ASCII-only text. The next step should stay strict: correct only clearly mappable non-ASCII punctuation and spacing characters, show the corrected result in the existing payload/body preview flow, and leave broader rewriting, translation, or server-side signature-contract changes out of scope.
