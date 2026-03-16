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
