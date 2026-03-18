## Stage 1 - fingerprint-based pow requirement contract
- Changes:
  - Added a fingerprint-based PoW requirement helper in [proof_of_work.py](/home/wsl/v2/forum_core/proof_of_work.py) so the lookup path can answer from a normalized signer fingerprint without first parsing the full armored public key.
  - Updated `/api/pow_requirement` in [web.py](/home/wsl/v2/forum_web/web.py) to accept `signer_fingerprint` directly, while keeping `public_key` as a compatibility fallback.
  - Added endpoint tests covering fingerprint input and the missing-input error path in [test_first_post_pow_submission.py](/home/wsl/v2/tests/test_first_post_pow_submission.py).
- Verification:
  - Ran `FORUM_ENABLE_UNSIGNED_POST_FALLBACK=0 python3 -m unittest /home/wsl/v2/tests/test_first_post_pow_submission.py`.
- Notes:
  - This stage only changes the preflight contract. Signed submission still performs the existing authoritative public-key and signature verification path.
