# Thread Native Task Roots - Step 4 Implementation Summary

## Stage 1 - Define typed root-thread model
- Changes:
  - Extended the canonical post parser to support `Thread-Type` on root posts and task-specific root metadata for `task` threads.
  - Added root-type helpers in the repository read model so later stages can detect task roots without special-casing ordinary threads.
  - Updated the canonical post record spec to document typed roots and the deferred future task-update boundary.
  - Grouped the Step 1-4 planning artifacts under `docs/plans/thread_native_task_roots/`.
- Verification:
  - `python -m unittest tests.test_thread_typed_roots`
- Notes:
  - Ordinary roots and replies remain valid; task metadata is only parsed for `Thread-Type: task` roots.

## Stage 2 - Make task creation and task-thread reading work through the native thread flow
- Changes:
  - Added a dedicated `/compose/task` entrypoint on top of the existing signed thread creation flow, with task-specific fields for status, ratings, dependencies, and sources.
  - Extended the browser-side canonical payload builder so `create_thread` can emit `Thread-Type: task` roots without changing the reply flow.
  - Rendered typed task metadata directly on `/threads/<thread-id>` and surfaced typed-root badges in the main board index.
  - Added a board-index link for composing task threads through the normal web interface.
- Verification:
  - `python -m unittest tests.test_task_thread_pages`
  - `python -m py_compile forum_read_only/web.py forum_read_only/api_text.py`
- Notes:
  - The task-thread creation path is generic at the protocol layer: future typed root kinds can reuse the same `Thread-Type` hook without changing reply semantics.

## Stage 3 - Derive planning/task browse surfaces from typed task threads
- Changes:
  - Added a task-thread read model that filters typed task roots out of the ordinary thread set without treating other typed roots as tasks.
  - Switched `/planning/task-priorities/` and `/planning/tasks/<task-id>` to derive from task-typed root threads instead of `records/tasks/`.
  - Seeded the existing curated task list into `records/posts/T01.txt` through `records/posts/T26.txt` as canonical task threads so the live planning pages stay populated after the source-of-truth shift.
  - Updated the planning templates to describe comment activity rather than linked external discussion threads.
- Verification:
  - `python -m unittest tests.test_task_priorities_page tests.test_task_thread_pages`
  - `python -m py_compile forum_read_only/web.py forum_read_only/task_threads.py`
- Notes:
  - Route stability stayed intact because the migrated task thread roots reuse the existing `T01`-style identifiers as their `Post-ID` values.

## Stage 4 - Harden typed root-thread model with tests and docs
- Changes:
  - Removed the superseded separate task-record runtime path (`forum_read_only/tasks.py`, `records/tasks/`, and the old task-record test fixture) so task-typed roots are the only canonical planning source in the live code path.
  - Updated repository/docs references to describe task metadata as root-thread state inside `records/posts/`, while keeping the old task-record spec only as a historical note.
  - Tightened the planning-page test fixture so a placeholder non-task typed root (`Thread-Type: proposal`) proves task-only surfaces do not accidentally include other future typed roots.
- Verification:
  - `python -m unittest tests.test_thread_typed_roots tests.test_task_thread_pages tests.test_task_priorities_page tests.test_compose_reply_page`
  - `python -m py_compile forum_read_only/web.py forum_read_only/repository.py forum_read_only/task_threads.py forum_read_only/api_text.py`
  - Manual WSGI smoke check for `/`, `/planning/task-priorities/`, `/planning/tasks/T01`, `/compose/task`, and `/threads/T01` on the live repo
- Notes:
  - The current architecture leaves room for future append-only task-update records without reintroducing a second canonical planning record family.
