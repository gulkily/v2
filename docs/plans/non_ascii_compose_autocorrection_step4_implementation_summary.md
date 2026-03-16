## Stage 1 - Add deterministic compose normalization
- Changes:
  - Extended [browser_signing.js](/home/wsl/v2/templates/assets/browser_signing.js) with a shared `normalizeComposeAscii` helper that rewrites a narrow set of non-ASCII punctuation and spacing characters into deterministic ASCII equivalents.
  - Updated the compose body flow so safe replacements are applied before payload preview and signing, while the backend ASCII-only submission contract remains unchanged.
  - Guarded browser-only startup in the module so the pure normalization helper can be imported in Node-based checks later.
- Verification:
  - Ran a temporary-module smoke import of `normalizeComposeAscii` and confirmed smart quotes, ellipses, and em dashes normalize to ASCII output.
  - Ran a second temporary-module smoke import and confirmed unsupported characters such as emoji remain detectable rather than being silently transliterated.
- Notes:
  - Stage 1 does not yet add the explicit remove-unsupported action; unsupported characters are only surfaced at this point.

## Stage 2 - Add explicit unsupported-character removal
- Changes:
  - Updated [compose.html](/home/wsl/v2/templates/compose.html) to include one shared `Remove Unsupported Characters` action and a dedicated normalization status note on existing compose pages.
  - Extended [browser_signing.js](/home/wsl/v2/templates/assets/browser_signing.js) so the shared compose flow enables that action only when unsupported characters remain, removes those characters through the same normalization helper, refreshes the payload preview, and keeps draft/signature state aligned.
- Verification:
  - Ran `python3 -m unittest tests.test_compose_thread_page tests.test_compose_reply_page tests.test_task_thread_pages`; all 11 tests passed.
  - Ran a temporary-module smoke import of `normalizeComposeAscii('emoji 🙂 test', { removeUnsupported: true })` and confirmed the helper returned ASCII-only text with one removed unsupported character.
- Notes:
  - The first slice removes unsupported characters exactly as typed; it does not attempt emoji aliases or semantic replacements.
