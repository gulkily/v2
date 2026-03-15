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
  - Pending.
- Verification:
  - Pending.
- Notes:
  - Pending.

## Stage 3 - Derive planning/task browse surfaces from typed task threads
- Changes:
  - Pending.
- Verification:
  - Pending.
- Notes:
  - Pending.

## Stage 4 - Harden typed root-thread model with tests and docs
- Changes:
  - Pending.
- Verification:
  - Pending.
- Notes:
  - Pending.
