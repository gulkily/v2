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
