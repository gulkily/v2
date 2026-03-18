## Stage 1
- Goal: add one deterministic browser-side normalization pass for clearly mappable non-ASCII compose characters before payload signing.
- Dependencies: approved Step 2; current browser signing flow in [`templates/assets/browser_signing.js`](/home/wsl/v2/templates/assets/browser_signing.js); existing compose pages rendered from [`forum_web/web.py`](/home/wsl/v2/forum_web/web.py).
- Expected changes: extend the shared compose normalization path with a small character-mapping helper for punctuation and spacing characters, define one helper contract such as `normalizeComposeAscii(text, { removeUnsupported = false }) -> { text, hadCorrections, hadUnsupported }`, and ensure canonical payload building uses the normalized text before ASCII enforcement; no database or API contract changes.
- Verification approach: manually load a compose page, type smart quotes/dashes/ellipses into the body, and confirm the payload preview shows deterministic ASCII replacements before signing.
- Risks or open questions:
  - keeping the mapping list narrow enough to stay predictable
  - avoiding accidental rewrites of characters that do not have obvious ASCII equivalents
- Canonical components/API contracts touched: browser compose/signing flow only; `/api/create_thread` and `/api/create_reply` remain unchanged.

## Stage 2
- Goal: add one explicit browser action to remove unsupported characters that remain after deterministic correction.
- Dependencies: Stage 1; current compose-page status/error messaging and sign-submit flow.
- Expected changes: extend the compose UI with one minimal action/control and status path that removes remaining unsupported non-ASCII characters from the body input, refreshes the derived payload preview, and keeps the final text aligned with what will be signed; planned contracts: reuse the same shared normalization helper with a `removeUnsupported` mode rather than adding a separate cleanup path; no backend changes.
- Verification approach: manually paste emoji-containing text into a compose page, confirm the normal sign path surfaces unsupported-character feedback, trigger the explicit removal action, and confirm the cleaned text can proceed through payload preview and signing.
- Risks or open questions:
  - keeping the action explicit enough that users understand content was removed
  - deciding whether the first slice should touch only message-body fields and not other user-entered compose inputs
- Canonical components/API contracts touched: existing compose page UI and browser signing script only; canonical payload and submission endpoints remain unchanged.

## Stage 3
- Goal: lock the behavior into focused frontend tests and operator/developer documentation.
- Dependencies: Stages 1-2; current compose/browser test coverage.
- Expected changes: add focused tests for deterministic punctuation correction, unsupported-character detection, and explicit removal behavior in the browser compose flow; update the relevant developer/operator docs or Step 4 summary to state that correction is browser-side and that unsupported characters are removable but not transliterated; no database changes.
- Verification approach: run targeted tests for the browser compose helper path, then repeat one manual thread/reply compose smoke check covering corrected punctuation and emoji removal.
- Risks or open questions:
  - choosing a stable test seam around browser-signing helpers without introducing a full frontend test framework
  - documenting the boundary clearly so future changes do not quietly expand correction into translation
- Canonical components/API contracts touched: browser compose helper tests; existing compose flow documentation; current create-thread/create-reply contract remains unchanged.
