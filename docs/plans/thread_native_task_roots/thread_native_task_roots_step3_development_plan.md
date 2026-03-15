## Stage 1
- Goal: define the canonical typed root-thread model, with `task` as the first subtype, and preserve a future-compatible boundary for append-only task updates.
- Dependencies: approved Step 2; existing canonical post record model; current thread grouping/read model.
- Expected changes: extend the root-post model with an explicit root-thread type plus subtype-specific task metadata such as status, ratings, and dependencies while keeping ordinary non-task roots valid; document that discussion replies remain replies and future authoritative task-state changes belong to a later task-update record family; planned helpers such as `parse_post_text(...) -> Post` with optional root type metadata, `root_thread_type(post) -> str | None`, `is_task_root(post) -> bool`, and `parse_task_dependencies(value) -> tuple[str, ...]`.
- Verification approach: load sample ordinary roots, typed task roots, and replies; confirm task metadata is parsed only for root posts of type `task`, and confirm non-task threads still resolve exactly as before.
- Risks or open questions:
  - how much task metadata belongs in the root post before the first slice becomes too close to full task-state management
  - whether malformed type/subtype headers should invalidate the whole thread or degrade to an ordinary thread in the first pass
- Canonical components/API contracts touched: canonical post record spec; typed root-thread parsing contract; task-root metadata boundary for future task-update records.

## Stage 2
- Goal: make task creation and task-thread reading work through the native thread flow.
- Dependencies: Stage 1; existing signed thread compose flow; existing thread view.
- Expected changes: extend thread creation so a maintainer can create a typed root thread of subtype `task`, render task metadata clearly on `/threads/<thread-id>`, and keep `/compose/reply` unchanged as the comment path for task discussion; planned helpers such as `render_task_thread_header(post) -> str`, `build_task_thread_defaults(...) -> TaskThreadDefaults`, and `render_thread_root_context(thread) -> str`.
- Verification approach: create one task-typed root thread, open its thread page, confirm the task metadata is visible there, and confirm replies on that thread continue to work through the normal reply flow.
- Risks or open questions:
  - how to keep task-thread presentation distinct without making ordinary thread rendering conditional spaghetti
  - how much creation-time structure to expose before the task-creation UX becomes a broader planning editor
- Canonical components/API contracts touched: typed root-thread creation flow; `/threads/<thread-id>`; normal reply flow for task comments.

## Stage 3
- Goal: derive planning/task browse surfaces from typed task threads and retire the separate task-record dependency for the core task view.
- Dependencies: Stage 1 and Stage 2; current planning/task index and detail surfaces.
- Expected changes: make planning index/detail pages derive from typed task roots instead of `records/tasks/`, keep task-specific navigation stable where possible, and ensure ordinary non-task threads or future non-task typed roots do not appear as tasks; planned helpers such as `load_task_threads(posts, moderation_state) -> list[Thread]`, `index_task_threads(threads) -> dict[str, Thread]`, and `render_task_detail(thread_id) -> str`.
- Verification approach: open the planning index and one task detail page, confirm they render from task threads, and confirm ordinary threads remain browseable but do not appear in task-only planning surfaces.
- Risks or open questions:
  - whether stable task identifiers should remain separate from `Post-ID` or collapse to task-thread root IDs in the first slice
  - how much compatibility work is needed for the current task routes while the canonical source of truth shifts
- Canonical components/API contracts touched: `/planning/task-priorities/`; `/planning/tasks/<task-id>` or successor task route; task-only typed-thread derivation contract.

## Stage 4
- Goal: harden the typed root-thread model and task subtype with focused tests and updated architecture docs.
- Dependencies: Stage 1 through Stage 3.
- Expected changes: add tests covering ordinary roots versus typed task roots, task-thread creation/readback, and planning-surface derivation from task threads, plus at least one placeholder non-task typed-root fixture to prove the parser boundary is extensible; update the canonical post spec and planning docs to record the typed-root direction and the deferred future task-update model; planned test targets such as `TaskRootParsingTests` and `ThreadNativeTaskPageTests`.
- Verification approach: run focused unittest modules for parsing and rendering, then manually smoke thread creation, task-thread reading, planning index/task detail, and reply-on-task behavior.
- Risks or open questions:
  - keeping the migration fixtures clear while both the old separate-task code and the new typed-root task model may coexist briefly during implementation
  - deciding which documentation should explicitly mark the separate task-record model as superseded for future work
- Canonical components/API contracts touched: canonical post record spec; typed root-thread rendering contract; planning surfaces derived from task threads; focused task-thread tests.
