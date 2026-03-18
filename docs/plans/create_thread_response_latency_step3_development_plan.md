1. Stage 1: Add phase-level timing visibility to the create-thread path
Goal: Make `/api/create_thread` report enough internal timing to identify whether latency is dominated by validation, git-backed write work, or post-index refresh.
Dependencies: Approved Step 2 only.
Expected changes: add lightweight timing capture around the major synchronous phases in the canonical thread-create path and emit that data through one minimal logging or debug-reporting seam; planned contracts such as `timed_submission_phase(name: str, sink: SubmissionTimingSink) -> ContextManager[None]`, `SubmissionTiming`, or `record_submission_timing(...) -> None`; keep the public success/error contract stable unless one clearly bounded debug-only surface is needed.
Verification approach: submit a representative thread in a disposable repo, inspect the emitted phase timings, and confirm the output distinguishes signature or PoW checks, git-backed commit work, and post-index refresh work.
Risks or open questions:
- Timing output must not expose sensitive payload contents.
- The observability seam should stay cheap enough that it does not materially change the latency being measured.
Canonical components/API contracts touched: `/api/create_thread`; `submit_create_thread(...)`; canonical commit-backed write path; operator-visible runtime logging or debug surface.

2. Stage 2: Reduce synchronous refresh cost for the common new-thread write path
Goal: Make the immediate post-commit refresh path do only the work needed for a newly added root post while preserving current read-after-write behavior.
Dependencies: Stage 1; existing derived post-index refresh contract.
Expected changes: narrow the create-thread refresh flow so it avoids broader rescans or git-history recomputation than a single new post requires; planned contracts such as `refresh_post_index_after_commit(..., touched_paths: tuple[str, ...]) -> None`, `refresh_index_for_new_post(...) -> None`, or `post_commit_timestamps_for_paths(...) -> dict[str, PostCommitTimestamps]`; preserve the current canonical write-first ordering.
Verification approach: submit a new thread and confirm the thread appears immediately on thread and index read surfaces while the measured refresh phase is materially smaller than the baseline.
Risks or open questions:
- The fast path must not let author, identity, or timestamp metadata drift for the touched post.
- The optimization should stay scoped to create-thread behavior rather than quietly redefining all refresh semantics at once.
Canonical components/API contracts touched: `commit_post(...)`; `refresh_post_index_after_commit(...)`; derived SQLite post-index metadata for touched posts.

3. Stage 3: Add focused regression coverage for latency-sensitive create-thread behavior
Goal: Lock in the optimized create-thread path and guard immediate visibility after successful writes.
Dependencies: Stages 1-2.
Expected changes: add focused tests around the create-thread write path, the narrowed post-index refresh behavior, and the expected immediate visibility of a newly created thread on existing read surfaces; include one deterministic assertion that timing data is emitted or capturable without depending on wall-clock thresholds.
Verification approach: run targeted tests plus a manual smoke pass that creates a thread and immediately loads the corresponding thread or board view.
Risks or open questions:
- Tests should assert correctness of the refreshed state, not brittle absolute latency numbers.
- Coverage must stay narrow enough to avoid turning this into a full performance-test harness feature.
Canonical components/API contracts touched: `/api/create_thread` tests; post-index refresh tests; immediate thread visibility on existing read surfaces.
