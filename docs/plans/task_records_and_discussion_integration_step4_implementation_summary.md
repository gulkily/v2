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
