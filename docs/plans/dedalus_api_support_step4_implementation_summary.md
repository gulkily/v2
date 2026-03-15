## Stage 1 - Dedalus env and dependency surface
- Changes:
  - Added `DEDALUS_API_KEY` to the canonical repo-root [.env.example](/home/wsl/v2/.env.example) so it participates in the existing `.env` and `./forum env-sync` workflow.
  - Added `dedalus-labs` to [requirements.txt](/home/wsl/v2/requirements.txt) as the minimal install surface for the shared server-side provider planned in later stages.
- Verification:
  - Ran a temp-repo smoke harness through `forum_core.runtime_env` with the current `.env.example`; confirmed `sync_env_defaults(...)` reported `added_count=4` from a partial `.env` and appended `DEDALUS_API_KEY=` to the synced output.
- Notes:
  - Kept model selection out of the env surface for now so the first slice stays aligned with the approved Step 2 scope.

## Stage 2 - Shared Dedalus LLM provider
- Changes:
  - Added [forum_core/llm_provider.py](/home/wsl/v2/forum_core/llm_provider.py) with a fixed v1 default model, explicit SDK and missing-key guards, client cleanup, and a plain-string `run_llm(...)` surface for later reuse.
  - Normalized provider failures into stable `LLMProviderError` messages so the route layer can translate them without depending on SDK internals.
- Verification:
  - Ran a mocked smoke harness against `run_llm(...)`; confirmed a synthetic completion returned `hello from dedalus` and an empty synthetic completion raised `Dedalus returned no text output.`.
- Notes:
  - The provider stays generic at the `messages` level for now, and the HTTP request shape decision remains in the route stage.
