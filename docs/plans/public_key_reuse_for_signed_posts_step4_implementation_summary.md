## Stage 1 - canonical public-key store contract
- Changes:
  - Added [public_keys.py](/home/wsl/v2/forum_core/public_keys.py) with one canonical `records/public-keys/` storage contract keyed by signer fingerprint.
  - Added helpers to store-or-reuse canonical public keys and to derive a signer fingerprint from a detached signature packet, which is the key read-path prerequisite for removing per-record `.pub.asc` files later.
- Verification:
  - Ran `python3 -m unittest /home/wsl/v2/tests/test_public_key_store.py`.
  - Confirmed repeated storage of the same public key resolves to one canonical path and that a detached signature resolves back to that canonical stored key.
- Notes:
  - This stage intentionally does not change any write or read surfaces yet; it only establishes the shared helper contract the later stages will consume.

## Stage 2 - reuse canonical key storage on signed writes
- Changes:
  - Updated the signed post, moderation, identity-link, merge-request, and profile-update write paths to store signatures plus a canonical public-key path rather than writing a new per-record `.pub.asc` sidecar every time.
  - Kept request-time `public_key` verification unchanged, but switched write responses and dry-run previews to report the canonical `records/public-keys/openpgp-<fingerprint>.asc` path.
  - Added focused write-side regression coverage for repeated signed thread creation and profile updates using the same key.
- Verification:
  - Ran `FORUM_ENABLE_UNSIGNED_POST_FALLBACK=0 python3 -m unittest /home/wsl/v2/tests/test_first_post_pow_submission.py /home/wsl/v2/tests/test_profile_update_submission.py`.
  - Confirmed repeated signed writes reuse one canonical stored key file and no longer create per-record `.txt.pub.asc` files in the write directories.
- Notes:
  - The read model still assumes sibling `.pub.asc` files at this point, so Stage 3 will refactor loaders to resolve public keys from detached signatures plus the canonical key store.

## Stage 3 - resolve canonical keys in read models
- Changes:
  - Updated post, moderation, profile-update, merge-request, and identity-link loaders to prefer the legacy sibling `.pub.asc` file when present and otherwise resolve the signer's canonical stored key by extracting the fingerprint from the detached signature.
  - Kept the read-side identity derivation behavior unchanged from the caller perspective: readers still surface `public_key_path`, `signer_fingerprint`, and derived identity information, but now against the canonical key store for newly written records.
- Verification:
  - Ran `FORUM_ENABLE_UNSIGNED_POST_FALLBACK=0 python3 -m unittest /home/wsl/v2/tests/test_thread_auto_reply.py /home/wsl/v2/tests/test_profile_update_submission.py /home/wsl/v2/tests/test_merge_request_submission.py`.
  - Confirmed new signed posts still render in thread/profile flows and merge-request records still load into the existing resolution/state model.
- Notes:
  - The legacy sibling-file fallback remains in place so older repositories stay readable without migration.
