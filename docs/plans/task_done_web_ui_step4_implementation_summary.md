## Stage 1 - filtered task priorities views
- Changes:
  - Added fixed task-priorities view modes so `/planning/task-priorities/` defaults to open tasks and exposes explicit `done` and `all` variants.
  - Extended the priorities template with view-navigation chips and view-specific copy while keeping the existing sortable table as the canonical planning index surface.
  - Added focused coverage for default open filtering and the new done/all views.
- Verification:
  - Ran `./forum test test_task_priorities_page.py`.
  - Confirmed the suite passed and covered default, done, and all-task priorities views.
- Notes:
  - This stage is read-only; task completion itself remains for the next stage.

## Stage 2 - task detail mark-done write flow
- Changes:
  - Added a narrow task-status write helper that updates only `Task-Status` on a task root, commits the changed task file, and rejects already-done or unknown tasks.
  - Extended the task detail page with a dedicated `mark task done` action and inline success/error feedback.
  - Added a task-specific POST route at `/planning/tasks/<task-id>/mark-done` and focused tests covering the action, success path, and already-done conflict path.
- Verification:
  - Ran `./forum test test_task_thread_pages.py`.
  - Ran `./forum test test_task_priorities_page.py`.
  - Confirmed the task detail action updates the canonical task root to `Task-Status: done` and the open/done planning filters still render correctly.
- Notes:
  - The task completion flow currently renders the updated task page directly after POST; broader navigation polish remains for the next stage.
