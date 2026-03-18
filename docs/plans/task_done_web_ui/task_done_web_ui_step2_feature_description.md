## Problem
The forum can already render task status on planning and task-detail pages, but there is no web UI path for changing that status when a task is complete, and the main planning view does not prioritize open work. The next slice should add the smallest useful browser flow for marking a task as done and make the planning views default to open tasks without expanding into general task editing, full lifecycle management, or a broader planning console.

## User Stories
- As a maintainer, I want to mark a task as done from the web UI so that I do not need to edit repository files manually for a common status change.
- As a maintainer, I want the completion action to live on the task detail page so that I can make the change while looking at one task's full context.
- As a planner, I want the default priorities view to show open tasks first so that completed work does not crowd the main planning list.
- As a reader, I want simple alternate filtered task views so that I can inspect open work and completed work separately.
- As a reader, I want the updated done state to appear on task-detail and task-priorities surfaces so that planning views stay coherent after the change.
- As a future implementer, I want the web flow to stay aligned with the canonical task record model so that later task-state work does not fork into a separate UI-only contract.

## Core Requirements
- The slice must add one minimal web UI path for marking an existing task as done.
- The default task-priorities page must show only open tasks.
- The slice must add two more simple filtered task views so users can switch among open, done, and complete task listings without introducing arbitrary filtering.
- The slice must keep the action scoped to the task detail flow rather than introducing broad inline editing across planning surfaces.
- The slice must update the canonical task state used by existing task read surfaces so the done state appears consistently after a successful change.
- The slice must show deterministic success or failure feedback so the user can tell whether the task status changed.
- The slice must avoid broader task editing, new task metadata fields, assignees, due dates, permissions work, or multi-step workflow management.

## Shared Component Inventory
- Existing task detail surface: extend `/planning/tasks/<task-id>` as the main place to initiate and confirm the status change because it already presents one task's full planning context.
- Existing task priorities surface: extend `/planning/task-priorities/` as the default open-task planning view and as the main place to expose the additional filtered task views.
- Existing canonical task record model: extend the current task-root status handling rather than inventing a separate completion-only state store or side channel.
- Existing browser write patterns: reuse the current explicit web-action style used elsewhere in the app so the completion action remains a focused flow rather than hidden mutable UI state.
- New task completion write surface: add one task-specific web action because there is no current UI or API path for changing task status from the browser.
- New filtered planning routes or query-backed variants: add only the minimal read-side surface needed to switch between open, done, and all-task views because the current planning page exposes one unfiltered listing.

## Simple User Flow
1. A reader opens `/planning/task-priorities/` and sees only open tasks by default, with simple links to the done and all-task views.
2. A maintainer opens a task detail page for one open task.
3. The page offers a focused action to mark the task as done.
4. The maintainer triggers the action and receives a deterministic success or failure result.
5. On success, the task detail page shows the task as done, the default priorities view no longer lists it, and the done or all-task views reflect the updated state.

## Success Criteria
- A maintainer can mark an existing task as done from the task detail page in the web UI.
- `/planning/task-priorities/` shows only open tasks by default.
- Users can access two additional simple filtered task views that show done tasks and all tasks.
- After a successful change, the done state is visible on the task detail page and in the appropriate filtered planning views, while the task disappears from the default open-task list.
- Failed completion attempts return a clear deterministic error without changing visible task state.
- The slice stays narrow by solving only the common "mark done" action plus three fixed planning views, not general task editing, arbitrary filtering, or broader planning workflow management.
