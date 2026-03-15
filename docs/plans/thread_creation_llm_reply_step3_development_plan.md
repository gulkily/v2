## Stage 1
- Goal: define the canonical runtime config for the feature flag and assistant-posting prerequisites.
- Dependencies: approved Step 2; existing repo-root `.env` / `.env.example` / `./forum env-sync` workflow; current `forum_core.runtime_env` behavior.
- Expected changes: add one disabled-by-default feature flag (for example `FORUM_ENABLE_THREAD_AUTO_REPLY=0`) to `.env.example`, document any minimal assistant-posting config needed by the server, and keep all new settings aligned with the existing non-overriding `.env` load path; prefer path-based assistant key configuration over embedding private key material directly in `.env`. Planned signatures/contracts: add small runtime-config readers near the posting/LLM integration surface, for example `def thread_auto_reply_enabled() -> bool` and `def get_thread_auto_reply_signing_config() -> AssistantSigningConfig`.
- Verification approach: run `./forum env-sync` against a repo with an older `.env`, confirm the new keys are appended once, confirm the feature remains disabled unless explicitly enabled, and confirm explicit process env values still override `.env`.
- Risks or open questions:
  - exact final names for the feature flag and assistant-signing settings
  - whether assistant signing should rely on filesystem key paths only in the first slice
- Canonical components/API contracts touched: `.env.example`; `forum_core.runtime_env`; repo-root `.env` precedence; `./forum env-sync` workflow.

## Stage 2
- Goal: add one shared backend helper that can generate and sign a canonical assistant reply for an existing thread.
- Dependencies: Stage 1; existing `forum_core.llm_provider` Dedalus helper; current canonical post parsing/validation and signed-post identity model.
- Expected changes: introduce a narrow helper module that accepts a newly created thread root, builds the helpful-reply prompt, calls Dedalus, constructs one canonical reply payload, signs it with the configured assistant identity, and returns stable result metadata or typed best-effort failure details without mutating thread-creation routing logic directly. Planned signatures/contracts: `def generate_thread_auto_reply(*, thread_post, repo_root: Path) -> AutoReplyAttemptResult`, `class AutoReplyAttemptResult`, and a small server-signing helper such as `def sign_ascii_payload(payload_text: str, *, signing_config: AssistantSigningConfig) -> SignedPayload`.
- Verification approach: cover prompt/result normalization and signing behavior with focused tests using mocked Dedalus output and fixture signing material, then manually confirm the helper can produce a valid signed reply payload for one stored thread in a disposable repo.
- Risks or open questions:
  - keeping prompt construction small and deterministic enough that outputs remain short and helpful
  - choosing a signing implementation that fits the current OpenPGP tooling without introducing a second identity model
- Canonical components/API contracts touched: `forum_core.llm_provider`; new auto-reply orchestration contract; canonical reply payload shape; assistant identity/signing flow.

## Stage 3
- Goal: wire the best-effort assistant reply path into successful thread creation.
- Dependencies: Stage 2; existing `submit_create_thread(...)` orchestration; current `create_thread` CGI/API entrypoints and submission result rendering.
- Expected changes: extend the thread-submission path so that after the root thread is stored successfully, it checks the feature flag and, when enabled, attempts one assistant reply generation/store cycle without rolling back the root thread on failure; reuse the existing reply validation/storage path as much as possible rather than writing reply files ad hoc. Add deterministic status reporting to the submission result contract so callers can tell whether auto-reply was disabled, created, or skipped/failed. Planned signatures/contracts: extend `SubmissionResult` with optional auto-reply fields such as `auto_reply_status`, `auto_reply_record_id`, and `auto_reply_message`; add a helper such as `def maybe_create_thread_auto_reply(...) -> AutoReplyAttemptResult`.
- Verification approach: exercise `/api/create_thread` and the CGI `create_thread` path with the feature disabled, enabled-and-successful, and enabled-but-failing; confirm the root thread is stored in all success cases and that only the enabled-successful case writes a reply record and commit.
- Risks or open questions:
  - whether the assistant reply should create its own git commit or be grouped with the original thread commit in the first slice
  - how much auto-reply status detail should be exposed in plain-text responses versus logs
- Canonical components/API contracts touched: `forum_cgi.service.submit_create_thread`; `forum_cgi.text.render_submission_result`; `forum_read_only.web` create-thread API route; `cgi-bin/create_thread.py` / `forum_cgi.entrypoint.py`.

## Stage 4
- Goal: lock the feature into tests and operator/developer documentation.
- Dependencies: Stages 1-3; current unittest harnesses for runtime env and WSGI API behavior.
- Expected changes: add focused tests for feature-flag parsing, successful auto-reply creation, best-effort failure behavior, and response/reporting shape with Dedalus mocked; add docs covering the new `.env` flag, assistant-signing prerequisites, and expected create-thread behavior when the feature is enabled. Planned signatures/contracts: test seams should target `submit_create_thread(...)`, WSGI `/api/create_thread`, and runtime-env parsing rather than relying on live network calls.
- Verification approach: run targeted unittest modules for runtime env, LLM integration, and create-thread behavior; manually compare the documented setup and output against a disposable-repo smoke test with the feature toggled on and off.
- Risks or open questions:
  - creating reliable signing fixtures for automated tests without making them brittle or environment-dependent
  - keeping docs clear about the difference between `DEDALUS_API_KEY`, the feature flag, and assistant-signing configuration
- Canonical components/API contracts touched: `tests/` submission and WSGI request patterns; `.env.example`; `docs/developer_commands.md`; create-thread result contract.
