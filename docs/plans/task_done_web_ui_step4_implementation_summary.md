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
