## Stage 1 - Canonical task record model
- Changes:
  - Added the canonical task record spec in `docs/specs/canonical_task_record_v1.md`.
  - Added repository task parsing and validation helpers in `forum_read_only/tasks.py`.
  - Seeded `records/tasks/` with the current curated task list as one human-readable record per task.
- Verification:
  - Ran `python -m py_compile forum_read_only/tasks.py`.
  - Ran a direct load smoke check through `load_tasks(Path("records/tasks"))` and confirmed `task_count = 26`, `first = T01`, `last = T26`, and `T07` resolves dependencies `("T02", "T06")`.
- Notes:
  - Task discussion links remain optional in the initial seed data; later stages will surface linked thread state when present.

## Stage 2 - Repository-backed planning index
- Changes:
  - Replaced the static planning-document route with a normal rendered `/planning/task-priorities/` page backed by `records/tasks/`.
  - Added a dedicated planning template plus a shared browser asset for sortable task tables.
  - Moved the planning table styles into `templates/assets/site.css` and kept the board-index entry point to the planning page.
- Verification:
  - Ran `python -m py_compile forum_read_only/web.py`.
  - Requested `/planning/task-priorities/` through the WSGI app and confirmed `200 OK`, `text/html; charset=utf-8`, the task-record stats copy, the `task_priorities.js` asset reference, and seeded task content.
  - Requested `/assets/task_priorities.js` through the WSGI app and confirmed `200 OK` with `text/javascript; charset=utf-8`.
- Notes:
  - The planning index now supports linked discussion-state rendering, but the dedicated task detail surface remains Stage 3.

## Stage 3 - Task detail view and discussion linkage
- Changes:
  - Added `/planning/tasks/<task-id>` as the canonical task detail route.
  - Linked task IDs, titles, and dependency references from the planning index into the new detail surface.
  - Added task-detail discussion summaries that point to the normal thread view and compose-reply flow when a task record declares `Discussion-Thread-ID`.
- Verification:
  - Ran `python -m py_compile forum_read_only/web.py`.
  - Requested `/planning/tasks/T01` through the WSGI app against the current repo and confirmed `200 OK` with the seeded task title.
  - Ran a temp-repo smoke check with one task record linked to `root-001` and confirmed `/planning/tasks/T99` renders the linked thread URL and compose-reply URL, while `/planning/tasks/T404` returns `404 Not Found` with the existing missing-resource copy.
- Notes:
  - The task detail page intentionally summarizes linked discussion state instead of embedding full thread rendering, so comments still live on the normal thread surface.

## Stage 4 - Focused tests and record-family docs
- Changes:
  - Added task-model tests covering structured parsing plus dependency validation failures.
  - Replaced the planning-page stub test with record-backed route coverage for the planning index, task detail view, linked discussion actions, unlinked tasks, and missing-task behavior.
  - Updated `records/README.md` so the new `tasks/` record family is discoverable beside the existing canonical record categories.
- Verification:
  - Ran `python -m unittest tests.test_task_records tests.test_task_priorities_page` and confirmed `Ran 8 tests ... OK`.
  - Manually requested `/planning/task-priorities/` and `/planning/tasks/T01` through the WSGI app against the current repo and confirmed both returned `200 OK` with `text/html; charset=utf-8`.
- Notes:
  - The current repo seed data still leaves discussion links optional; linked-discussion behavior is covered in temp-repo tests until canonical task-discussion threads are added to the repo.
