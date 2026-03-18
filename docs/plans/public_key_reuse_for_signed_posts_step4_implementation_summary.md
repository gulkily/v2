## Stage 1 - canonical public-key store contract
- Changes:
  - Added [public_keys.py](/home/wsl/v2/forum_core/public_keys.py) with one canonical `records/public-keys/` storage contract keyed by signer fingerprint.
  - Added helpers to store-or-reuse canonical public keys and to derive a signer fingerprint from a detached signature packet, which is the key read-path prerequisite for removing per-record `.pub.asc` files later.
- Verification:
  - Ran `python3 -m unittest /home/wsl/v2/tests/test_public_key_store.py`.
  - Confirmed repeated storage of the same public key resolves to one canonical path and that a detached signature resolves back to that canonical stored key.
- Notes:
  - This stage intentionally does not change any write or read surfaces yet; it only establishes the shared helper contract the later stages will consume.
