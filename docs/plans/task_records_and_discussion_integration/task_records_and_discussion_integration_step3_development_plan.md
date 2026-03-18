## Stage 1
- Goal: define the canonical human-readable task-record model and seed the repository with task records.
- Dependencies: approved Step 2; existing text-record parsing pattern used for posts and moderation.
- Expected changes: add one dedicated task record family under `records/tasks/`, document the minimal header/body shape for task metadata and linked discussion, add shared parsing/loading/validation helpers, and migrate the current curated priorities data out of the standalone HTML document into canonical task files; planned helpers such as `parse_task_text(raw_text, *, source_path=None) -> TaskRecord`, `load_tasks(records_dir) -> list[TaskRecord]`, and `validate_task_graph(tasks) -> None`.
- Verification approach: load the seeded task records from a temp repo, confirm ratings and dependency references validate deterministically, and confirm the default task order is preserved.
- Risks or open questions:
  - whether task edits remain in-place for now or need append-only update records in a later loop
  - choosing the smallest required header set without making future task views too dependent on freeform body text
- Canonical components/API contracts touched: new `records/tasks/` record family; repository text-record parsing contract; task metadata headers for ID, ratings, dependencies, sources, and optional discussion-thread linkage.

## Stage 2
- Goal: replace the static priorities document with a repository-backed planning index.
- Dependencies: Stage 1.
- Expected changes: make `/planning/task-priorities/` render from loaded task records instead of from hard-coded HTML rows, move the table presentation into normal reader templates/assets, and keep client-side sorting as a view concern rather than the source of truth; planned helpers such as `render_task_priorities_page(tasks, *, threads, moderation_state) -> str` and `build_task_index_rows(tasks, thread_index, moderation_state) -> list[TaskIndexRow]`.
- Verification approach: open the planning index in a seeded repo, confirm task titles, ratings, dependencies, and source labels come from task records, and confirm sortable headers still work without changing the canonical order on first load.
- Risks or open questions:
  - preserving the curated default ordering while still allowing client-side sort behavior
  - deciding how much discussion state the index should show before the detail page exists
- Canonical components/API contracts touched: `/planning/task-priorities/`; shared page/template rendering contract; browser-side table-sorting asset behavior.

## Stage 3
- Goal: add a task detail view that joins task metadata with the existing discussion-thread model.
- Dependencies: Stage 1 and Stage 2.
- Expected changes: add one task page such as `/planning/tasks/<task-id>`, render task metadata plus dependency links and source context, surface linked discussion-thread state when `Discussion-Thread-ID` is present, and link into the existing thread/reply views without creating a planning-specific comment flow; planned helpers such as `render_task_detail(task_id) -> str`, `find_task(tasks, task_id) -> TaskRecord | None`, and `summarize_task_discussion(task, thread_index, moderation_state) -> TaskDiscussionSummary`.
- Verification approach: open a task with a linked discussion thread, confirm the page links to the existing thread view and shows stable discussion summary state, confirm a task without a linked thread still renders cleanly, and confirm unknown task IDs return the current missing-resource behavior.
- Risks or open questions:
  - how much thread summary to surface before the task page becomes a second thread renderer
  - how to present missing, hidden, or locked linked threads without making task records feel broken
- Canonical components/API contracts touched: new `/planning/tasks/<task-id>` read surface; existing `/threads/<thread-id>` discussion surface; existing compose/reply entry points as the write path for comments.

## Stage 4
- Goal: harden the feature with focused tests and record-family documentation.
- Dependencies: Stage 1 through Stage 3.
- Expected changes: add task-record parsing and validation tests, add route/rendering tests for the planning index and task detail view, add discussion-link coverage for linked and unlinked tasks, and update repository navigation docs so the new record family is discoverable; planned test targets such as `TaskRecordModelTests` and `TaskPlanningPageTests`.
- Verification approach: run focused unittest modules covering task loading and planning-page rendering, then manually smoke the planning index and one task detail page in the local reader.
- Risks or open questions:
  - keeping the temp-repo fixtures small while still covering dependency and linked-thread edge cases
  - deciding whether validation failures should fail the whole planning view or degrade more softly for malformed task records
- Canonical components/API contracts touched: task-record validation contract; planning index and detail routes; `records/README.md` navigation for canonical record families.
