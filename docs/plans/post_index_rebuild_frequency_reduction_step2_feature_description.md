## Problem
Ordinary indexed reads can still trigger a full post-index rebuild whenever the repo head has advanced, even when the existing index shape is still usable. The next slice should reduce those unnecessary full rebuilds by treating compatible head drift as incremental catch-up work instead of rebuild-required state.

## User Stories
- As a reader, I want ordinary board, thread, and profile reads to avoid unnecessary full reindex waits so that normal browsing stays responsive after routine repo activity.
- As an operator, I want full rebuilds to happen only when the derived index is actually incompatible or unsafe to advance so that rebuild frequency better matches real maintenance needs.
- As a maintainer, I want the system to preserve the current canonical post-index lifecycle and read surfaces so that this slice narrows rebuild policy without introducing a second indexing model.
- As a future performance investigator, I want the stale-index decision to distinguish schema incompatibility from ordinary newer-commit drift so that rebuild causes are diagnosable from concrete signals.

## Core Requirements
- When the existing post index remains schema-compatible, newer repo commits must no longer force an immediate full rebuild on ordinary indexed reads.
- The feature must preserve full rebuilds as the fallback when the index is missing, structurally incompatible, or otherwise unsafe to advance incrementally.
- The stale-index decision must make schema compatibility an explicit first-class factor rather than relying only on the current schema-version equality check.
- Canonical indexed read surfaces must continue to read from the same derived post index and return coherent board, thread, and profile data after catch-up completes.
- Existing rebuild and operation-visibility signals must remain the operator-facing diagnosis path for why a full rebuild happened versus an incremental catch-up.

## Shared Component Inventory
- Post-index readiness and recovery lifecycle in [forum_core/post_index.py](/home/wsl/v2/forum_core/post_index.py): extend the canonical `ensure_post_index_current(...)`, readiness metadata, and refresh/rebuild decision path because this is where ordinary indexed reads currently fall from head drift into full rebuilds.
- Existing incremental post-index refresh path in [forum_core/post_index.py](/home/wsl/v2/forum_core/post_index.py): reuse and extend the current commit-by-commit catch-up behavior rather than introducing a second recovery model, because Step 1 approved fast-forwarding the existing derived index when it is still structurally usable.
- Indexed board and thread ordering surfaces in [forum_web/web.py](/home/wsl/v2/forum_web/web.py): preserve the current board and thread reads that already depend on the canonical derived post index, because these are the user-facing surfaces affected when unnecessary rebuilds fire.
- Indexed profile and related read surfaces in [forum_web/web.py](/home/wsl/v2/forum_web/web.py): preserve the current profile-backed read flow for the same reason; the slice should improve stale-index recovery without creating alternate profile read logic.
- Existing rebuild logs and operation timing surfaces in [forum_core/operation_events.py](/home/wsl/v2/forum_core/operation_events.py) and [forum_web/web.py](/home/wsl/v2/forum_web/web.py): reuse the current operator-facing diagnostics so rebuild-versus-catch-up behavior remains visible without a separate status system.

## Simple User Flow
1. A reader opens a board, thread, profile, or other page that depends on the derived post index.
2. The system detects that the repo has advanced beyond the index metadata.
3. If the existing index remains schema-compatible, the system incrementally catches the index up from the indexed head to the current head instead of rebuilding from scratch.
4. If the index is incompatible or unsafe to advance, the system falls back to the existing full rebuild path.
5. The requested page renders from the refreshed canonical index, and operators can still tell which recovery path was taken.

## Success Criteria
- Ordinary repo head drift no longer causes a full post-index rebuild when the existing index is still schema-compatible and incrementally recoverable.
- Full rebuilds remain reserved for missing, incompatible, or otherwise unsafe index states.
- Covered indexed-read pages continue to return coherent results after stale-index recovery.
- Operator-visible diagnostics make it clear whether a stale read triggered incremental catch-up or a full rebuild, and why.
