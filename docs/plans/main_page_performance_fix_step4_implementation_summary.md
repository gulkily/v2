## Stage 1 - Align native read cookie safety
- Changes:
  - Updated PHP-native board and thread route guards to reuse the shared cache-busting credential policy instead of rejecting every cookie unconditionally.
  - Expanded the shared identity-hint cache-safe path contract so `/threads/...` requests with only `forum_identity_hint` remain eligible for public fast paths.
  - Added PHP host tests covering board and thread native reads with identity-hint cookies and unexpected-cookie fallback behavior.
- Verification:
  - Ran `python3 -m pytest -q tests/test_php_host_cache.py`.
  - Result: `21 passed in 12.83s`.
- Notes:
  - The thread case required widening the shared cookie-safety helper, not just the native route guards, because the helper previously marked all thread routes as cache-busting when any cookie was present.
