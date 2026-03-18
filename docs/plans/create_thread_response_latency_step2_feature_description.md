## Problem
`/api/create_thread` currently takes too long to return on this deployment even with `FORUM_ENABLE_THREAD_AUTO_REPLY=0`, which means the remaining synchronous root-thread write path is doing more work than users should wait on. The next slice should make canonical thread creation feel materially faster while preserving the current signed write contract and immediate read-after-write behavior.

## User Stories
- As a user submitting a new thread, I want `/api/create_thread` to return quickly so that posting feels responsive instead of stalled.
- As a node operator, I want thread creation to stay canonical and durable so that latency improvements do not weaken validation, signed-write rules, or repository consistency.
- As a maintainer, I want the latency reduction to focus on derived follow-up work in the current write path so that the fix stays narrow and does not require a broader queue or write-contract redesign.
- As a future performance investigator, I want the create-thread path to expose a clear timing breakdown so that later regressions can be diagnosed from concrete phase data rather than guesswork.

## Core Requirements
- The slice must preserve the current canonical `/api/create_thread` contract for accepted thread submissions, including the existing validation and durable repository write semantics.
- The slice must materially reduce synchronous create-thread latency on instances where thread auto-reply is disabled.
- The slice must preserve immediate read-after-write behavior for existing thread and index read surfaces unless later evidence proves that requirement must change.
- The slice must make the dominant create-thread phases observable through lightweight timing instrumentation.
- The slice must avoid turning this loop into a broader async-job, queue, or unrelated submission-pipeline redesign.

## Shared Component Inventory
- Existing canonical thread-create API: reuse and extend `/api/create_thread` as the same browser-facing and operator-facing write surface because the latency issue is in the current contract, not a missing endpoint.
- Existing canonical write pipeline: reuse the current signed submission flow and repository-backed post storage because thread acceptance, validation, and commit-backed durability remain the source of truth.
- Existing derived post index: extend the current post-index refresh behavior rather than adding a second cache or alternate derived read model, because the current synchronous refresh is the likely latency target.
- Existing read surfaces backed by current repository or index state: preserve board index, thread pages, and other immediate post-submit reads as the canonical consumers that motivate keeping read-after-write behavior coherent.
- Existing timing and operational visibility surface: add minimal observability to the current create-thread path because there is no current phase-level latency reporting for this flow, and the feature needs one shared source of truth for future diagnosis.

## Simple User Flow
1. User submits a signed or unsigned root thread through the existing compose flow.
2. Server performs the current canonical acceptance work and stores the thread durably.
3. Server completes the remaining synchronous follow-up work quickly enough that the API response returns without a long stall.
4. User receives a normal successful thread-create response.
5. User can immediately open the new thread or other read surfaces and see state consistent with the successful write.

## Success Criteria
- `/api/create_thread` returns materially faster than the current baseline on this deployment when thread auto-reply is disabled.
- Accepted thread submissions still use the existing canonical validation and repository-backed durability model.
- Existing immediate post-submit reads continue to show the newly created thread without requiring a manual repair or delayed follow-up step.
- The create-thread path exposes enough phase-level timing data to identify whether remaining latency comes from validation, git-backed write work, or derived-state refresh work.
