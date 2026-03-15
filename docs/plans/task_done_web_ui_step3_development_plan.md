## Stage 1
- Goal: add the fixed planning filters so the default task-priorities page shows open tasks and exposes done/all views.
- Dependencies: approved Step 2; existing `/planning/task-priorities/` render path; current task status read model.
- Expected changes: extend the task-priorities route with one minimal view selector such as a path variant or query-backed mode, filter task rows by the existing `Task-Status` value, and add simple navigation among open, done, and all-task views; planned helpers such as `task_filter_mode_from_request(...) -> str` and `filter_task_threads(threads, *, mode) -> list[Thread]`.
- Verification approach: load the default priorities page and confirm only non-`done` tasks appear, then load the done and all-task views and confirm each shows the expected subset with stable sort behavior.
- Risks or open questions:
  - choosing the smallest URL shape that keeps the three views explicit without adding a generic filtering framework
  - deciding whether any status other than `done` should count as open in this slice
- Canonical components/API contracts touched: `/planning/task-priorities/`; task-priorities template/CSS; task status read contract.

## Stage 2
- Goal: add a focused web UI action on the task detail page for marking one task as done.
- Dependencies: Stage 1; existing `/planning/tasks/<task-id>` page; current canonical task-root status field.
- Expected changes: extend the task detail page with one explicit completion action, add one minimal write surface that changes `Task-Status` on the canonical task root from its current value to `done`, and return deterministic success or failure output; planned helpers such as `renderTaskDoneAction(thread) -> str`, `submit_mark_task_done(task_id, repo_root) -> TaskStatusUpdateResult`, and `update_task_root_status(task_id, *, status="done") -> str`.
- Verification approach: open a task detail page for an open task, trigger the action, and confirm a successful response updates the canonical task state while attempts against unknown or already-done tasks return stable errors.
- Risks or open questions:
  - whether the write should be a small dedicated form POST or a minimal API call from the task page
  - how to keep the write path narrow without implying broader task-editing support
- Canonical components/API contracts touched: `/planning/tasks/<task-id>`; new task-status write surface; canonical `Task-Status` field on task roots.

## Stage 3
- Goal: complete readback, navigation, and focused regression coverage for done-task behavior.
- Dependencies: Stage 1 and Stage 2.
- Expected changes: ensure successful completion immediately reads back as done on the task detail page, disappears from the default open-task view, and remains visible in done/all views; add focused tests for filters, task-detail action visibility, successful completion, and deterministic failure states; planned helpers such as `is_task_open(thread) -> bool` and `completion_redirect_target(task_id) -> str`.
- Verification approach: mark one task done, confirm the task detail page shows the updated state, confirm the task is absent from the default priorities view, confirm it appears in done/all views, and run targeted unittest modules for task priorities and task detail flows.
- Risks or open questions:
  - avoiding flaky assertions if the success flow redirects instead of rendering inline feedback
  - deciding how much of the completion control should remain visible for already-done tasks
- Canonical components/API contracts touched: task-detail readback surface; filtered planning views; focused task page and priorities tests.
