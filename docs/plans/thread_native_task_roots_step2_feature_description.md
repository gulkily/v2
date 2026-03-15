## Problem
Tasks currently sit outside the native thread and reply model, which makes discussion about them feel grafted on rather than inherent to the forum. The next slice should make a task itself be a special kind of thread root so task discussion uses the existing thread/reply flow directly, while leaving room for future append-only task-update records instead of committing long-term to mutable root metadata.

## User Stories
- As a reader, I want a task to be a normal thread root so that I can read task context and discussion in one place.
- As a commenter, I want to reply to a task through the existing reply flow so that task discussion behaves like every other forum conversation.
- As a maintainer, I want task threads to carry structured planning metadata so that status, ratings, and dependencies are not hidden in prose conventions alone.
- As a future implementer, I want the task-thread model to leave room for append-only task-update records so that authoritative task state can evolve later without relying forever on editing the root thread.
- As a reader of ordinary threads, I want task threads to remain recognizable as planning entities so that general discussion views do not become ambiguous.

## Core Requirements
- The slice must define one explicit typed thread-root model inside the canonical post/thread family, with `task` as the first supported subtype.
- The slice must let task discussion use the existing reply model rather than a planning-specific comment system.
- The slice must make task-specific metadata visible on task read surfaces while keeping ordinary non-task threads valid and readable.
- The slice must keep subtype-specific metadata scoped cleanly enough that future special thread types can be added without redesigning the root-thread model again.
- The slice must keep the architecture compatible with future append-only task-update records even if the first slice still reads task state primarily from the task root.
- The slice must avoid separate task records, generic project-management workflows, assignees, due dates, or full task-update history in the first pass.

## Shared Component Inventory
- Existing canonical post record family: extend the thread-root record shape with an explicit root-thread type discriminator because tasks should become the first typed root post rather than a one-off special case.
- Existing thread view: extend `/threads/<thread-id>` as the primary task read surface because task discussion should stay on the normal thread page.
- Existing reply compose flow: reuse `/compose/reply` unchanged as the canonical write path for task comments.
- Existing thread creation flow: extend the signed thread compose path so a maintainer can create a typed root thread with the `task` subtype rather than introducing a separate task-creation subsystem.
- Existing board/index rendering: extend current index surfaces only where needed to distinguish typed task threads from ordinary threads, instead of creating a second planning-only browse model first.
- Existing planning views: task-priorities and related planning pages may later become derived views over task threads, but that derivation is downstream of the core task-thread model and should not redefine the canonical source of truth.

## Simple User Flow
1. A maintainer creates a new typed root thread with subtype `task`, task metadata, and an initial task description.
2. A reader opens the task thread and sees both the structured task context and the discussion beneath it.
3. A commenter replies through the normal reply flow, and those replies become the task's discussion.
4. Other readers return to the same task thread and see one canonical place for both task state and task conversation.
5. Future slices can add other typed root threads and append-only task-update records without changing the fact that task discussion lives on the thread.

## Success Criteria
- A task can be created and rendered as a typed thread root within the existing post/thread family.
- Task comments use the normal reply flow with no separate planning-comment implementation.
- Task threads visibly carry structured planning metadata while ordinary non-task threads remain valid and readable.
- The root-thread model is explicit enough that future special thread types can be added without redefining the core task slice.
- The design leaves a coherent future path for append-only task-update records instead of locking the system into root-thread mutation as the only long-term state mechanism.
- The slice stays narrow by making tasks discussion-native now without also implementing full task lifecycle management.
