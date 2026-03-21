## Problem
Legitimate full post-index rebuilds currently take too long once they start, which increases operator wait time and stretches user-visible delays on request-triggered rebuild paths. The next slice should make the existing rebuild flow materially faster without changing when rebuilds happen or turning the work into a broader indexing redesign.

## User Stories
- As an operator, I want a legitimate full post-index rebuild to finish faster so that maintenance and recovery work blocks the system for less time.
- As a user, I want pages that depend on a legitimate rebuild to resume sooner so that rebuild-required reads feel less disruptive.
- As a maintainer, I want the speedup to stay inside the current rebuild contract so that the fix remains narrow and does not require a broader background-job or indexing-model redesign.
- As a future performance investigator, I want the rebuild path to expose a clear phase breakdown so that later regressions can be diagnosed from concrete timing data rather than guesswork.

## Core Requirements
- The slice must materially reduce the duration of a legitimate full post-index rebuild within the current canonical rebuild flow.
- The slice must preserve the current correctness contract of the derived post index so that faster rebuilds do not produce incomplete or inconsistent indexed data.
- The slice must not change the conditions that trigger a rebuild; rebuild-frequency policy remains out of scope for this feature.
- The slice must preserve the existing read surfaces that depend on the post index rather than introducing an alternate read model or a separate cache.
- The slice must make the dominant rebuild phases observable through lightweight timing or operation-visibility data.

## Shared Component Inventory
- Existing canonical full rebuild flow: reuse and extend the current post-index rebuild path as the same maintenance surface because the problem is rebuild cost inside the current contract, not a missing rebuild entrypoint.
- Existing post-index-backed read surfaces: preserve board, thread, and post reads that depend on the current derived index because they are the canonical consumers affected when rebuilds take too long.
- Existing request-triggered rebuild handling: preserve the current rebuild-required request behavior because this feature is about reducing rebuild duration, not changing request-time rebuild policy.
- Existing operator performance visibility surface: reuse and extend the current operation timing/reporting surface as the shared source of truth for measuring rebuild duration before and after the change.

## Simple User Flow
1. A legitimate stale-index condition requires a full post-index rebuild.
2. The system starts the existing canonical rebuild flow.
3. The rebuild completes faster than it does today while producing the same coherent derived index state.
4. The blocked maintenance task or request proceeds using the refreshed index.
5. An operator can inspect the rebuild timing breakdown to confirm where time was spent.

## Success Criteria
- A legitimate full post-index rebuild completes materially faster than the current baseline on the same repository state.
- Post-index-backed read surfaces continue to return coherent results after the rebuild completes.
- The feature does not change the rebuild-triggering rules or depend on a new background execution model.
- Rebuild timing output is detailed enough to identify whether remaining latency is concentrated in one dominant phase or distributed across multiple phases.
