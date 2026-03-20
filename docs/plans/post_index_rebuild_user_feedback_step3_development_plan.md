## Stage 1
- Goal: Define one canonical request-time status contract for indexed reads so the web layer can tell when a request is blocked on a stale-index rebuild.
- Dependencies: Approved Step 2; existing `ensure_post_index_current(...)`, `tracked_operation(...)`, and indexed-read helpers in `forum_core/post_index.py`.
- Expected changes: conceptually extend the post-index readiness path with a small result or callback seam that distinguishes normal indexed reads from rebuild-triggered reads; planned signature updates may include adding an optional status recorder argument to `ensure_post_index_current(repo_root: Path, *, status_callback: Callable[[dict[str, str]], None] | None = None)` and propagating that through the indexed-read entry points that currently trigger rebuilds.
- Verification approach: manual smoke check with a forced stale index to confirm the request path can detect “reindex in progress” before returning content; existing recent-operation entries still record the rebuild.
- Risks or open questions:
  - Need to keep the seam lightweight so indexed reads that do not rebuild stay unchanged.
  - Need to avoid leaking raw stale-check internals into user-facing copy.
- Canonical components/API contracts touched: `forum_core/post_index.py` indexed-read lifecycle; `forum_core/operation_events.py` tracked operation model.

## Stage 2
- Goal: Show explicit user-facing feedback on the canonical indexed-read pages when a request is waiting on a rebuild.
- Dependencies: Stage 1; current board, thread, and profile render entry points in `forum_web/web.py`; existing page shell and templates in `templates/`.
- Expected changes: conceptually thread the Stage 1 status through the page render path and render one shared waiting or refresh notice in the existing page shell or selected page templates; planned function signature updates may include optional request-status context on render helpers such as `render_board(...)`, `render_thread(thread_id: str, *, request_status: RequestStatus | None = None)`, and profile render entry points where indexed reads are used.
- Verification approach: manual smoke checks for board, thread, and profile requests with a forced rebuild to confirm the user sees an explicit “refreshing forum data” style state instead of only a long blank wait; non-rebuild requests still render normally.
- Risks or open questions:
  - Need one presentation pattern that works across covered pages without creating route-specific variants.
  - Need to confirm which indexed-read pages are in the first slice if any route proves to have a materially different render lifecycle.
- Canonical components/API contracts touched: `forum_web/web.py` page rendering entry points; existing templates and site page shell.

## Stage 3
- Goal: Add regression coverage for the new request-status contract and the covered user-facing feedback surfaces.
- Dependencies: Stages 1-2; existing web and operation tests.
- Expected changes: extend unit and request tests to cover rebuild-triggered indexed reads, normal indexed reads, and operator correlation expectations; likely touch tests around board rendering, profile rendering, and background-operation events without adding new storage models.
- Verification approach: run targeted automated tests for post-index, board/profile page rendering, and operation-event visibility; manual smoke check once more with a forced stale index.
- Risks or open questions:
  - Test setup must force the stale-index path deterministically without making the suite slow or brittle.
  - Need to avoid over-coupling template assertions to exact copy if wording changes later.
- Canonical components/API contracts touched: `tests/test_post_index.py`, route-level page tests, and operation-event tests.
