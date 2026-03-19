1. Stage 1: Add one shared operation-timing recorder and recent-event store
Goal: Create the canonical timing model and persistence seam for live, completed, and failed operations with short-retention recent history.
Dependencies: Approved Step 2; existing phase-timing callbacks in write and post-index code; existing SQLite usage patterns in `forum_core/post_index.py`.
Expected changes: add one small shared module for operation lifecycle recording and retention cleanup; define conceptual contracts such as `start_operation(...) -> OperationHandle`, `record_operation_step(...) -> None`, `complete_operation(...) -> None`, and `fail_operation(...) -> None`; add one local recent-event SQLite store, potentially separate from the post-index database, with operation rows plus structured step-timing payloads; keep existing plain logs available as secondary output.
Verification approach: create one disposable operation record in a test or smoke helper, confirm it is visible while running, finalized on completion, and removed by retention cleanup when aged out.
Risks/Open questions:
- Keep the recorder cheap enough that it does not materially distort the timings it captures.
- Make the event schema sparse enough to avoid retaining sensitive request data.
Canonical components/API contracts touched: shared timing model; local SQLite-backed recent-event store; existing timing-callback seams.

2. Stage 2: Instrument full HTTP request operations and route existing write-path phase timings into the shared recorder
Goal: Ensure every HTTP request has one operation record with full-request timing and any available named sub-step timings.
Dependencies: Stage 1; WSGI/request dispatch in `forum_web/web.py`; existing create-thread, reply, profile-update, and post-index timing callbacks.
Expected changes: wrap request handling with one operation lifecycle; capture request method, path or operation name, start state, completion state, and failure state; thread the shared recorder through existing timing-callback-enabled write paths so their named phases land in the operation record instead of only ad hoc logs; add planned helper seams such as `record_http_request_operation(environ, handler) -> Response` or `request_operation_context(...)`.
Verification approach: load `/`, `/instance/`, and one representative write endpoint in a disposable repo and confirm the recent store contains request records with total duration plus known sub-step timings where available.
Risks/Open questions:
- Avoid double-counting timings when a request already records nested phase callbacks.
- Keep request classification stable enough that recent slow operations are readable in the report.
Canonical components/API contracts touched: `forum_web/web.py` request dispatch; current CGI submission flows; existing timing callbacks in `forum_cgi/service.py`, `forum_cgi/posting.py`, and `forum_core/post_index.py`.

3. Stage 3: Instrument selected non-request startup and maintenance tasks with the same operation model
Goal: Make startup/readiness and maintenance-style work visible in the same recent-operation store, including incomplete and failed runs.
Dependencies: Stage 1; existing non-request entry points such as post-index readiness, rebuild, or maintenance helpers.
Expected changes: add operation lifecycle recording to the selected non-request entry points; reuse the same step-timing recorder for post-index rebuild or refresh sub-steps; ensure long-running tasks remain visible while active and finalize on success or failure; add conceptual helper seams such as `run_tracked_operation(name, kind, fn)` for non-request code paths.
Verification approach: trigger one cold-start or forced-rebuild path in a disposable repo and confirm an in-progress operation becomes visible and later completes with step timings.
Risks/Open questions:
- Some startup flows may have multiple entry points; keep the first slice focused on the ones operators actually encounter.
- Avoid turning this stage into exhaustive instrumentation of every maintenance helper.
Canonical components/API contracts touched: post-index startup or rebuild entry points; shared operation recorder; existing post-index phase timing seams.

4. Stage 4: Add a lightweight recent slow operations report to the current operator-facing surface
Goal: Expose recent in-progress, failed, and completed slow operations through one in-app report without building a broader dashboard.
Dependencies: Stages 1-3; existing `/instance/` or closely related operator-facing page.
Expected changes: extend the current operator-facing page or add one adjacent route that reads from the recent-event store and renders recent operations sorted by duration or recency; show operation name, state, started time, total duration, and expandable or inline named sub-step durations; support a simple “recent slow operations” view first without charts or deep filtering.
Verification approach: open the report after exercising a few requests and one non-request task, confirm recent operations render with readable sub-step timings and clearly distinguish running, failed, and completed states.
Risks/Open questions:
- Keep the page small enough that it remains an operational aid rather than a new admin UI.
- Choose defaults that surface useful slow operations without hiding important failures.
Canonical components/API contracts touched: existing operator-facing instance or status surface; recent-event store read path.

5. Stage 5: Add focused regression coverage for recorder lifecycle, retention, and report rendering
Goal: Lock in the shared operation model and report behavior with deterministic tests.
Dependencies: Stages 1-4.
Expected changes: add focused tests for operation start/update/complete or fail lifecycle, short-retention cleanup, request instrumentation capture, non-request task capture, and recent-report rendering; include one deterministic assertion that existing write-path phase timings are persisted into the shared operation record.
Verification approach: run focused unit and request-level tests that assert presence of operation records and expected step names without depending on brittle wall-clock thresholds.
Risks/Open questions:
- Test coverage should assert shape and lifecycle correctness, not absolute latency numbers.
- Keep fixtures small so retention and report tests remain fast and comprehensible.
Canonical components/API contracts touched: shared operation recorder; recent-event store; operator-facing report; request and non-request timing entry points.
