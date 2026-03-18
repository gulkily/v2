## Problem
The forum now has a useful task-priorities page, but the planning data still lives in page markup and is disconnected from the repository-backed discussion model. The next slice should move planning state into human-readable task records and connect each task to the existing thread/reply system so planning becomes maintainable, inspectable, and discussable without introducing a separate database or a second comment model.

## User Stories
- As a maintainer, I want each planning task stored as a human-readable canonical record so that I can review and edit planning state directly in git.
- As a reader, I want to browse prioritized tasks and open a task-specific discussion so that planning context and conversation stay connected.
- As a commenter, I want task discussion to use the same thread and reply behavior as the rest of the forum so that planning comments do not require a separate workflow.
- As a future implementer, I want task data separated from presentation markup so that planning views can be regenerated, validated, and extended without hand-editing HTML tables.
- As an operator, I want the priorities view to reflect linked discussion state so that active and inactive tasks are easy to distinguish.

## Core Requirements
- The slice must define one human-readable canonical task-record format stored in the repository.
- The slice must make the task-priorities view render from task records rather than from hard-coded HTML rows.
- The slice must let each task link to one normal discussion thread and surface the linked discussion state consistently in planning views.
- The slice must reuse the existing thread/reply model for comments rather than creating a planning-specific comment system.
- The slice must avoid database storage, assignees, due dates, kanban behavior, permissions work, or a broader project-management feature set.

## Shared Component Inventory
- Existing planning priorities page: extend `/planning/task-priorities/` as the canonical task index, but make it a read model over task records plus linked thread state rather than a static document.
- Existing thread view: reuse `/threads/<thread-id>` as the canonical discussion surface for task conversation because the comment system already exists there.
- Existing compose surfaces: reuse `/compose/thread` and `/compose/reply` as the write path for task discussion so planning comments stay aligned with the current posting model.
- Existing repository-backed read pattern: extend the same text-record reading approach already used for posts, moderation, and profiles so task state remains text-native and git-visible.
- New task detail surface: add one dedicated task page because the priorities index and generic thread view are not sufficient together for showing task metadata, dependency context, and linked discussion entry points in one place.
- Existing API surfaces: no current API route renders planning tasks, and this slice does not require a separate task write API to be useful.

## Simple User Flow
1. A maintainer adds or updates a human-readable task record in the repository.
2. A reader opens `/planning/task-priorities/` and sees the task list rendered from those records, including dependency and discussion context.
3. The reader opens one task's detail page to understand the task, its current priority signals, and whether a discussion thread is linked.
4. If discussion exists, the reader follows the linked thread and uses the normal reply flow to comment; if not, the task still remains readable as planning state.
5. Future readers return to the planning views and see the same task metadata together with current linked discussion activity.

## Success Criteria
- A maintainer can add or revise planning tasks through human-readable repository records without editing HTML page markup.
- `/planning/task-priorities/` renders its task list from canonical task records and shows linked discussion state for tasks that have it.
- A task detail view presents one task's metadata, dependencies, and linked discussion entry point in a stable read surface.
- Task discussion uses the existing thread and reply model rather than a second planning-specific comment implementation.
- The slice stays narrow: it improves planning storage and discussion linkage without expanding into full project-management behavior.
