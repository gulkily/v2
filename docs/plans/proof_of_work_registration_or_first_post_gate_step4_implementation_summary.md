## Stage 1 - Define PoW policy and first-post detection boundary
- Changes:
  - Added canonical first-post PoW config helpers for feature-flag and difficulty parsing.
  - Added a helper that determines whether a signed fingerprint still needs first-post PoW by checking for an existing identity bootstrap record.
  - Added `.env.example` defaults for the new feature flag and difficulty.
- Verification:
  - Ran `python -m unittest tests.test_proof_of_work tests.test_runtime_env`.
- Notes:
  - First-post detection is currently defined as "no identity bootstrap record exists for this signer fingerprint."
