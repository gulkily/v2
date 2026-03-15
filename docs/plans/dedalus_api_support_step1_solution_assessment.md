## Problem Statement
Choose the smallest useful way to let developers and operators configure a Dedalus Labs API key in the repo-root `.env` file and make Dedalus available to future forum tasks without exposing secrets or scattering provider logic across entrypoints.

### Option A: Extend the existing repo-root `.env` workflow and add one shared server-side Dedalus access layer
- Pros:
  - Matches the `~/penelope` pattern directly: `DEDALUS_API_KEY` lives in `.env` and `.env.example`, loads once at startup, and is consumed through one backend helper.
  - Reuses the current `forum_core.runtime_env` and `./forum env-sync` workflow instead of inventing a second config path.
  - Keeps the API key server-side while making Dedalus reachable from future CGI, WSGI, and CLI-backed tasks through one contract.
  - Gives later Dedalus features one consistent place for auth, defaults, and error handling.
- Cons:
  - Adds a small shared abstraction before the first task-specific Dedalus feature is implemented.
  - Likely adds a new dependency or shared HTTP client code to maintain.
  - Still requires later feature work to define the concrete task APIs.

### Option B: Add only `DEDALUS_API_KEY` to `.env` and let each future feature call Dedalus directly
- Pros:
  - Smallest immediate code change.
  - Keeps the current slice narrowly focused on configuration only.
  - Lets each future feature choose SDK or raw HTTP independently.
- Cons:
  - Repeats auth, defaults, and error handling across features.
  - Makes it easier for browser code, CGI paths, and scripts to drift into inconsistent integration patterns.
  - Weak fit for the goal of making Dedalus a shared backend capability.

### Option C: Keep Dedalus outside the app and rely on per-shell exports or browser-direct calls
- Pros:
  - Fastest path for one-off experiments.
  - Avoids adding a shared backend integration upfront.
- Cons:
  - Does not give the repo a first-class `.env` workflow beyond manual operator setup.
  - Browser-direct usage risks exposing the API key.
  - Per-shell exports fragment configuration across entrypoints and diverge from the proven `~/penelope` pattern.

## Recommendation
Recommend Option A: extend the existing repo-root `.env` workflow with `DEDALUS_API_KEY` and add one shared server-side Dedalus access layer.

This is the smallest coherent adaptation of the `~/penelope` pattern for this repo. It builds on the `.env` support that already exists here, keeps the secret server-side, and makes future Dedalus-backed tasks easier to add without duplicating setup. The next steps should stay narrow: document `DEDALUS_API_KEY` in `.env.example`, keep `./forum env-sync` as the operator sync path, load the key through the current startup env helper, and add one backend-facing Dedalus module that later features can reuse. Defer optional model-selection settings until the first concrete Dedalus task actually needs them.
