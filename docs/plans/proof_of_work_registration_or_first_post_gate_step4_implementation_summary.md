## Stage 1 - Define PoW policy and first-post detection boundary
- Changes:
  - Added canonical first-post PoW config helpers for feature-flag and difficulty parsing.
  - Added a helper that determines whether a signed fingerprint still needs first-post PoW by checking for an existing identity bootstrap record.
  - Added `.env.example` defaults for the new feature flag and difficulty.
- Verification:
  - Ran `python -m unittest tests.test_proof_of_work tests.test_runtime_env`.
- Notes:
  - First-post detection is currently defined as "no identity bootstrap record exists for this signer fingerprint."

## Stage 2 - Add canonical PoW verification to signed posting APIs
- Changes:
  - Added a canonical first-post PoW message format and verifier using SHA-256 leading-zero-bit difficulty.
  - Extended signed create-thread/create-reply API requests to accept `pow_stamp`.
  - Enforced PoW verification for signed first-post submissions, including dry-run preview requests, when the feature flag is enabled.
- Verification:
  - Ran `python -m unittest tests.test_proof_of_work tests.test_first_post_pow_submission`.
- Notes:
  - The accepted stamp format is `v1:<hex nonce>`.
  - Verification binds the work to signer fingerprint, exact `Post-ID`, and configured difficulty.

## Stage 3 - Extend browser signing compose flow to compute and submit PoW
- Changes:
  - Exposed PoW enablement and difficulty to compose pages through existing data attributes.
  - Extended the shared browser signing script to derive the public-key fingerprint, solve the SHA-256 PoW in the browser, show progress in existing status text, and submit `pow_stamp`.
  - Added compose-page coverage for the new PoW settings hooks.
- Verification:
  - Ran `python -m unittest tests.test_compose_thread_page tests.test_compose_reply_page tests.test_first_post_pow_submission`.
- Notes:
  - When the feature flag is enabled, signed thread and reply compose both compute PoW before preview/submit; the server still decides whether the stamp is required for that signer.
