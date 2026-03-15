## Stage 1 - Runtime config surface
- Changes:
  - Added a disabled-by-default `FORUM_ENABLE_THREAD_AUTO_REPLY=0` feature flag to [.env.example](/home/wsl/v2/.env.example).
  - Added commented path-based assistant signing key settings to [.env.example](/home/wsl/v2/.env.example) so the feature can use server-side key files without embedding private key material directly in `.env`.
- Verification:
  - Ran `python3 -m unittest tests.test_runtime_env`; the existing runtime-env suite still passed after the new `.env.example` entries were added.
- Notes:
  - This stage only establishes the canonical operator config surface; no thread behavior changes yet.

## Stage 2 - Shared auto-reply generation and signing helper
- Changes:
  - Added [auto_reply.py](/home/wsl/v2/forum_cgi/auto_reply.py) with feature-flag parsing, assistant signing config loading, prompt construction, ASCII reply normalization, canonical reply payload building, and a `generate_thread_auto_reply(...)` helper that returns a signed reply payload.
  - Extended [signing.py](/home/wsl/v2/forum_cgi/signing.py) with `sign_detached_payload(...)`, implemented through the repo-bundled `openpgp.min.mjs` and `node`, so server-side assistant replies can be signed without relying on an unavailable `gpg-agent`.
- Verification:
  - Ran `python3 -m py_compile forum_cgi/auto_reply.py forum_cgi/signing.py`.
  - Ran a disposable-repo smoke harness with generated OpenPGP keys and mocked `run_llm(...)`; confirmed the helper produced a canonical reply payload and that `verify_detached_signature(...)` accepted the generated signature.
- Notes:
  - The helper is intentionally not wired into thread creation yet; that integration happens in the next stage.
