1. Stage 1: Make full-rebuild timing output precise enough to isolate the dominant cost
Goal: Confirm which sub-step dominates legitimate full post-index rebuild time and expose enough detail to measure improvement safely.
Dependencies: Approved Step 2 only.
Expected changes: extend the current canonical rebuild timing surface so full rebuilds report the expensive git-history derivation work with enough fidelity to compare before and after optimization; planned contracts may stay within the existing `rebuild_post_index(...)` timing callback shape or add one narrowly scoped helper such as `record_post_index_phase(...) -> None`; no change to rebuild-triggering rules or indexed read contracts.
Verification approach: run a representative full rebuild on a disposable repo, inspect emitted phase timings, and confirm the output clearly distinguishes timestamp derivation from post loading, identity loading, row upserts, and SQLite commit work.
Risks or open questions:
- Timing detail must stay cheap enough that it does not distort the rebuild cost being measured.
- The baseline may reveal more than one meaningful bottleneck, which would require keeping later stages narrowly ordered by payoff.
Canonical components/API contracts touched: `rebuild_post_index(...)`; operation timing or recent-operations visibility for maintenance work.

2. Stage 2: Narrow full-rebuild timestamp derivation to avoid the current broad git-history scan pattern
Goal: Reduce legitimate full rebuild duration by replacing the current expensive timestamp derivation approach with a more focused derivation strategy inside the existing rebuild flow.
Dependencies: Stage 1; current canonical full rebuild contract.
Expected changes: conceptually refactor full rebuild timestamp derivation so it reuses a narrower per-path or otherwise less redundant git-history lookup model instead of the broad current scan; planned contracts may include reshaping `post_commit_timestamps(repo_root) -> dict[str, PostCommitTimestamps]`, extending `post_commit_timestamps_for_paths(...) -> dict[str, PostCommitTimestamps]`, or adding one shared helper that both rebuild and incremental refresh can call; preserve the same derived `created_at` and `updated_at` semantics for indexed posts.
Verification approach: run a full rebuild on representative repo state, confirm the timing phase for commit timestamps is materially smaller than baseline, and spot-check indexed posts to confirm timestamp fields remain coherent.
Risks or open questions:
- The optimized derivation must not change timestamp semantics for renamed, edited, or older posts without an explicit product decision.
- Sharing logic between full rebuild and incremental refresh should reduce redundancy without quietly widening refresh behavior beyond this feature.
Canonical components/API contracts touched: `post_commit_timestamps(...)`; `post_commit_timestamps_for_paths(...)`; `rebuild_post_index(...)`; indexed post timestamp fields in the existing SQLite post index.

3. Stage 3: Add focused regression coverage for optimized full rebuild timing and correctness
Goal: Lock in the faster full rebuild path while protecting the correctness of indexed timestamp data and post-rebuild reads.
Dependencies: Stages 1-2.
Expected changes: add focused tests around the optimized full rebuild timestamp path, including one deterministic assertion that the rebuild still populates coherent timestamp fields and one narrow assertion that the timing output still reports the key rebuild phases without depending on brittle wall-clock thresholds.
Verification approach: run targeted post-index and maintenance-operation tests, then perform one manual smoke check that forces a legitimate rebuild and confirms indexed reads succeed afterward.
Risks or open questions:
- Tests should verify correctness and timing-surface presence, not absolute elapsed time.
- Coverage must stay narrow enough to avoid turning this feature into a full performance benchmarking harness.
Canonical components/API contracts touched: `tests/test_post_index.py`; rebuild-operation visibility tests; existing indexed read surfaces exercised after rebuild.
