## Stage 1
- Goal: Make stale-index recovery decisions explicit enough to separate schema-incompatible rebuilds from schema-compatible head drift.
- Dependencies: Approved Step 2; existing readiness and metadata flow in `forum_core/post_index.py`.
- Expected changes: conceptually extend the current readiness model so it reports a recovery path or reason instead of only a single rebuild-required boolean; planned contracts may include expanding `PostIndexReadiness` with an explicit compatibility or recovery-decision field and adding a helper such as `determine_post_index_recovery_path(...) -> PostIndexRecoveryDecision`; database changes stay limited to derived-index metadata, such as storing a schema-compatibility signal alongside the existing indexed head and count metadata.
- Verification approach: manual smoke check against current, head-drifted, and schema-mismatched index states to confirm the readiness decision distinguishes “incremental catch-up” from “full rebuild.”
- Risks or open questions:
  - Need a compatibility signal narrow enough to avoid unnecessary rebuilds without silently allowing incompatible index shapes.
  - Need to preserve existing cold-start and missing-index behavior as full rebuild cases.
- Canonical components/API contracts touched: `PostIndexReadiness`; `post_index_readiness(...)`; `ensure_post_index_current(...)`; derived metadata stored in the existing SQLite post index.

## Stage 2
- Goal: Fast-forward a schema-compatible index from its indexed head to the current head instead of rebuilding from scratch.
- Dependencies: Stage 1; existing incremental refresh behavior in `refresh_post_index_after_commit(...)`.
- Expected changes: add one canonical catch-up path that walks commits between the indexed head and current head, derives touched paths per commit, and reuses the existing incremental refresh semantics for each step; planned contracts may include helpers such as `commit_range(repo_root: Path, start_head: str, end_head: str) -> tuple[str, ...]`, `commit_touched_paths(repo_root: Path, commit_id: str) -> tuple[str, ...]`, and `catch_up_post_index_between_heads(repo_root: Path, *, index: PostIndex, start_head: str, end_head: str, timing_callback: PhaseTimingCallback | None = None) -> None`; `ensure_post_index_current(...)` would choose this path only when Stage 1 marks the index as compatible.
- Verification approach: manual smoke check on a repo where HEAD advances through representative post and profile-related commits, then confirm indexed board/profile reads succeed without triggering a full rebuild timing pattern.
- Risks or open questions:
  - Need to decide when non-fast-forward history, missing indexed head metadata, or unsupported touched paths should abort catch-up and fall back to full rebuild.
  - Commit-by-commit catch-up must preserve the same derived author, identity, and username-root state as a full rebuild on the same final repo state.
- Canonical components/API contracts touched: `ensure_post_index_current(...)`; `refresh_post_index_after_commit(...)`; git-history helpers in `forum_core/post_index.py`; canonical indexed read surfaces that already call `ensure_post_index_current(...)`.

## Stage 3
- Goal: Lock in the new recovery policy with focused regression coverage and operator-visible path distinction.
- Dependencies: Stages 1-2; existing post-index and operation-visibility tests.
- Expected changes: extend tests to cover schema-compatible head drift, schema-incompatible fallback rebuilds, and coherent indexed reads after catch-up; add narrow assertions that diagnostics distinguish incremental catch-up from full rebuild, likely through readiness data, logs, or existing operation metadata rather than new product surfaces.
- Verification approach: run targeted post-index tests for head drift, profile-related commits, and fallback rebuild cases; manually force one compatible head-drift scenario and one incompatible scenario to confirm the operator-visible signals show different recovery paths.
- Risks or open questions:
  - Tests must prove path selection and final indexed correctness without over-coupling to exact log text.
  - Need to keep diagnostics lightweight so the new distinction does not become a second status system.
- Canonical components/API contracts touched: `tests/test_post_index.py`; readiness or startup tests around stale-index recovery; existing operator-facing logging or operation-event surfaces.
