## Stage 1 - fingerprint-based pow requirement contract
- Changes:
  - Added a fingerprint-based PoW requirement helper in [proof_of_work.py](/home/wsl/v2/forum_core/proof_of_work.py) so the lookup path can answer from a normalized signer fingerprint without first parsing the full armored public key.
  - Updated `/api/pow_requirement` in [web.py](/home/wsl/v2/forum_web/web.py) to accept `signer_fingerprint` directly, while keeping `public_key` as a compatibility fallback.
  - Added endpoint tests covering fingerprint input and the missing-input error path in [test_first_post_pow_submission.py](/home/wsl/v2/tests/test_first_post_pow_submission.py).
- Verification:
  - Ran `FORUM_ENABLE_UNSIGNED_POST_FALLBACK=0 python3 -m unittest /home/wsl/v2/tests/test_first_post_pow_submission.py`.
- Notes:
  - This stage only changes the preflight contract. Signed submission still performs the existing authoritative public-key and signature verification path.

## Stage 2 - switch browser preflight to signer fingerprints
- Changes:
  - Updated [browser_signing.js](/home/wsl/v2/templates/assets/browser_signing.js) so the compose flow derives the fingerprint from the locally available public key and sends `signer_fingerprint` to `/api/pow_requirement` instead of uploading the full armored public key on that preflight call.
  - Exported a small browser helper for uppercase fingerprint derivation and added a focused asset test in [test_browser_signing_normalization.py](/home/wsl/v2/tests/test_browser_signing_normalization.py).
- Verification:
  - Ran `FORUM_ENABLE_UNSIGNED_POST_FALLBACK=0 python3 -m unittest /home/wsl/v2/tests/test_browser_signing_normalization.py /home/wsl/v2/tests/test_first_post_pow_submission.py`.
- Notes:
  - Signed submission itself is unchanged here; only the advisory PoW lookup path is lighter.

## Stage 3 - regression coverage and authoritative submission guard
- Changes:
  - No further product code was needed beyond Stages 1 and 2; this stage locked in the boundary that `/api/pow_requirement` is the fast advisory path while signed submission remains authoritative.
  - Reused the updated endpoint and browser tests, plus compose-page coverage, as the regression gate for the new preflight contract.
- Verification:
  - Ran `FORUM_ENABLE_UNSIGNED_POST_FALLBACK=0 python3 -m unittest /home/wsl/v2/tests/test_browser_signing_normalization.py /home/wsl/v2/tests/test_first_post_pow_submission.py /home/wsl/v2/tests/test_compose_thread_page.py /home/wsl/v2/tests/test_compose_reply_page.py`.
- Notes:
  - Submission-time `public_key` plus signature verification and first-post PoW enforcement are unchanged; only the browser preflight request is lighter.
