## Stage 1 - Runtime config surface
- Changes:
  - Added a disabled-by-default `FORUM_ENABLE_THREAD_AUTO_REPLY=0` feature flag to [.env.example](/home/wsl/v2/.env.example).
  - Added commented path-based assistant signing key settings to [.env.example](/home/wsl/v2/.env.example) so the feature can use server-side key files without embedding private key material directly in `.env`.
- Verification:
  - Pending.
- Notes:
  - This stage only establishes the canonical operator config surface; no thread behavior changes yet.
