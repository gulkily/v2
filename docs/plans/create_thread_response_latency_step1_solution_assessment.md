## Problem Statement
Choose the smallest useful way to make `/api/create_thread` return materially faster on this deployment, where `FORUM_ENABLE_THREAD_AUTO_REPLY=0`, without weakening the canonical signed thread-write path.

### Option A: Keep the current write contract and reduce post-commit index refresh cost on the create-thread path
- Pros:
  - Targets the most likely remaining hot path after thread creation because the request still performs a git-backed commit and then calls `refresh_post_index_after_commit(...)`.
  - Preserves the current browser and server contract for canonical thread creation.
  - Can stay narrow if the work is limited to the incremental refresh path for newly added post records.
  - Fits the current architecture because the endpoint already writes canonically first and then updates derived read-side state.
- Cons:
  - Needs measurement to confirm which part of the post-commit flow is actually dominant.
  - May still leave some fixed git overhead in place even after the index refresh is reduced.
  - Requires care not to let the read model drift from the canonical repository state.

### Option B: Leave indexing behavior intact and focus on git-command and signature-validation micro-optimizations
- Pros:
  - Keeps the current read-model update behavior fully unchanged.
  - Could reduce latency if git invocation overhead or signing checks are unexpectedly dominant in this environment.
  - Smaller local code changes are possible if one obvious hot subprocess is identified.
- Cons:
  - Risks chasing secondary costs while leaving the heavier post-commit read-model work untouched.
  - Gives a less reliable payoff because the current create-thread path still refreshes derived state immediately after every commit.
  - Could lead to several small optimizations instead of one change that materially moves request time.

### Option C: Defer post-index refresh out of the request path and rebuild lazily on the next read
- Pros:
  - Could cut create-thread latency sharply by removing the derived-state update from the synchronous write path.
  - Keeps canonical git-backed storage authoritative because only the read-model timing changes.
  - Smaller than a full background-job system if existing lazy-rebuild behavior can absorb the delay.
- Cons:
  - Makes the most recent thread potentially absent from indexed read surfaces until a later refresh occurs.
  - Changes consistency semantics for pages that currently expect the index to be current immediately after a successful write.
  - Broader product and correctness tradeoffs than a targeted performance fix to the current incremental refresh path.

## Recommendation
Recommend Option A: keep the current canonical thread-create contract and reduce the synchronous post-commit index refresh cost on the create-thread path.

On this instance, `FORUM_ENABLE_THREAD_AUTO_REPLY=0`, so `/api/create_thread` is not waiting on any LLM call or second reply write. The remaining synchronous path is the root thread validation/signature flow, one git-backed canonical write, and the immediate post-index refresh. That makes the derived-state update the best first place to look before changing endpoint consistency semantics.

The next step should stay narrow:

- Add lightweight timing instrumentation around signature verification, PoW verification, `git add`, `git commit`, `rev-parse`, and `refresh_post_index_after_commit(...)`.
- Use those timings to confirm whether the current incremental index refresh is dominated by `load_posts(...)`, `load_identity_context(...)`, `post_commit_timestamps(...)`, or another subprocess-heavy helper.
- Optimize the index refresh for the common create-thread case first, especially if it currently rescans all posts or recomputes git history more broadly than needed for one new root post.
- Preserve immediate read-after-write behavior for canonical thread pages unless measurements prove that a synchronous refresh cannot be made fast enough.
- Leave broader async indexing and unrelated assistant-reply changes out of scope for this slice.

That is the smallest coherent path because it targets the likely bottleneck that still exists with auto-reply disabled, while preserving the current product contract that a successful thread submission is both canonical and immediately visible to derived read surfaces.
