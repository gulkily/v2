## Problem Statement
Choose the smallest useful way to let a user mark a task as done from the web UI without turning the next loop into full task editing, lifecycle management, or a generic admin console.

### Option A: Add a focused "mark done" action on the task detail page
- Pros:
  - Smallest and most obvious user flow because the action lives on the page already dedicated to one task.
  - Keeps the write scope narrow: one status transition for one task.
  - Avoids overloading the priorities table with row-level controls and confirmation states.
  - Fits the current product shape where read pages can link into small explicit write actions.
- Cons:
  - Adds a task-specific write control before there is a broader task-editing model.
  - Requires deciding how the page communicates signer requirements and read-after-write feedback.

### Option B: Add a "mark done" control directly in each task-priorities row
- Pros:
  - Fastest bulk workflow for someone triaging many tasks from the planning view.
  - Keeps the planning page actionable instead of read-only.
- Cons:
  - Cramps a write action into an already dense table.
  - Makes confirmation, error display, and signer state harder to present cleanly.
  - Increases the risk of accidental status changes from the highest-traffic planning surface.

### Option C: Add a general task-edit page and include status changes there
- Pros:
  - Creates a future home for status, ratings, dependencies, and other task metadata changes.
  - Avoids introducing a one-off action that later has to be folded into a broader editor.
- Cons:
  - Larger scope than the current user story.
  - Pulls the next loop toward full task editing before the simplest status-change flow is proven useful.
  - Requires more UI and copy decisions than a focused "mark done" action.

## Recommendation
Recommend Option A: add a focused "mark done" action on the task detail page.

This is the narrowest coherent slice. It gives the web UI one explicit completion action in the place where a user is already looking at a single task, while avoiding both a crowded planning table and the broader scope of a general task editor.
