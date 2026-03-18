## Stage 1
- Goal: extend the canonical runtime config and dependency surface for Dedalus.
- Dependencies: approved Step 2; existing repo-root `.env` / `.env.example` / `./forum env-sync` workflow; current `requirements.txt`.
- Expected changes: document `DEDALUS_API_KEY` in `.env.example`, keep it aligned with the existing env-loading path and sync workflow, and add the minimal Dedalus client dependency to the repo install surface; no database changes. Planned signatures/contracts: no new runtime-env API expected beyond the current `load_repo_env(...)` and `sync_env_defaults(...)` flow.
- Verification approach: run `./forum env-sync` against a repo state missing the new key, confirm `.env` gains `DEDALUS_API_KEY` without overwriting existing values, and confirm explicit process environment values still override `.env`.
- Risks or open questions:
  - whether the first slice should document only `DEDALUS_API_KEY` or also an optional future model override
  - keeping the dependency surface small in a repo that currently has very few install requirements
- Canonical components/API contracts touched: `.env.example`; `requirements.txt`; repo-root `.env` precedence; `./forum env-sync` operator workflow.

## Stage 2
- Goal: add one shared server-side Dedalus LLM helper that the API route and later features can reuse.
- Dependencies: Stage 1; current `forum_core` shared-backend module pattern; `~/penelope` Dedalus helper approach.
- Expected changes: introduce a new shared helper module (for example `forum_core/llm_provider.py`) that loads `DEDALUS_API_KEY`, initializes a sync Dedalus client, executes one minimal text-generation/chat call with a fixed default model, closes client resources, and returns a normalized text result plus stable provider errors; no browser or route changes yet. Planned signatures: `def run_llm(messages: list[dict[str, str]]) -> str`, `def get_llm_model() -> str`, `class LLMProviderError(RuntimeError)`.
- Verification approach: run focused tests or a small harness with the provider mocked for success/failure cases, then do one manual call with a configured key to confirm the helper returns non-empty text.
- Risks or open questions:
  - exact default OpenAI-prefixed model alias for v1 if model selection is not exposed yet
  - whether the minimal reusable input contract should be a generic `messages` list or a narrower prompt-only helper internally
- Canonical components/API contracts touched: new shared server-side LLM provider contract; `DEDALUS_API_KEY` runtime config; future Dedalus-backed task integration surface.

## Stage 3
- Goal: expose one ready-to-use HTTP API path for a real server-side Dedalus LLM call.
- Dependencies: Stage 2; existing `/api/` namespace in `forum_read_only.web`; current JSON request parsing and text response conventions.
- Expected changes: add a new POST API route (for example `/api/call_llm`) that accepts a minimal JSON request, validates required prompt/message input, calls the shared provider helper, and returns a stable text/plain response with the model used and generated output; add a dedicated renderer/helper in the current API text layer if needed. Planned signatures: `def render_api_call_llm(environ) -> tuple[str, str]`, `def render_llm_result_text(*, model: str, output_text: str) -> str`.
- Verification approach: manually POST to the new route with a configured key and confirm a 200 response containing generated text; repeat with missing input and missing `DEDALUS_API_KEY` to confirm stable error responses.
- Risks or open questions:
  - whether the baseline request shape should accept `messages` directly or just `prompt` plus optional `system_prompt`
  - unauthenticated cost exposure if this endpoint is deployed publicly before a stronger access-control story exists
- Canonical components/API contracts touched: `/api/` POST JSON contract; `forum_read_only.web` route dispatch; `forum_read_only.api_text` text response surface.

## Stage 4
- Goal: lock the Dedalus config and minimal LLM API path into tests and operator documentation.
- Dependencies: Stages 1-3; current unittest-based WSGI request harness patterns.
- Expected changes: add focused tests for the new API route with the provider mocked, cover missing-config and invalid-request cases, update env-related tests if `.env.example` coverage changes, and document the new setup/call flow in the repo’s operator/developer docs with one example request. Planned signatures/contracts: test harnesses should exercise the WSGI `application(...)` path rather than a parallel server entrypoint.
- Verification approach: run targeted unittest discovery patterns for runtime env coverage and the new API route, then manually compare the documented example request/response against the actual route behavior.
- Risks or open questions:
  - choosing stable test seams around a new external SDK dependency without making tests network-dependent
  - deciding the smallest durable documentation surface for a capability that is intentionally low-level and developer-oriented
- Canonical components/API contracts touched: `tests/` WSGI request patterns; `.env.example` operator guidance; repo developer/operator command documentation; new minimal LLM API contract.
