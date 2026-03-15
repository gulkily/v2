## Stage 1 - Dedalus env and dependency surface
- Changes:
  - Added `DEDALUS_API_KEY` to the canonical repo-root [.env.example](/home/wsl/v2/.env.example) so it participates in the existing `.env` and `./forum env-sync` workflow.
  - Added `dedalus-labs` to [requirements.txt](/home/wsl/v2/requirements.txt) as the minimal install surface for the shared server-side provider planned in later stages.
- Verification:
  - Ran a temp-repo smoke harness through `forum_core.runtime_env` with the current `.env.example`; confirmed `sync_env_defaults(...)` reported `added_count=4` from a partial `.env` and appended `DEDALUS_API_KEY=` to the synced output.
- Notes:
  - Kept model selection out of the env surface for now so the first slice stays aligned with the approved Step 2 scope.
