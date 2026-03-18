## Problem Statement
Choose the smallest useful way to preserve in-progress thread and reply drafts across accidental reloads or navigation, while showing a visible last-saved timestamp and avoiding a larger draft-sync system.

### Option A: Add local browser draft autosave to the existing shared compose page
- Pros:
  - Smallest coherent slice because thread and reply composition already share one template and one browser module.
  - Prevents the specific failure mode in the user story without adding new backend routes, record types, or auth questions.
  - Can scope draft keys by compose context such as new thread vs. reply target, so multiple drafts do not overwrite each other.
  - Makes the last-saved timestamp immediate and local, which matches the requirement even when the user has not submitted anything yet.
  - Can clear the stored draft after a successful signed submission so stale text does not unexpectedly reappear.
- Cons:
  - Drafts live only in one browser on one device.
  - Needs careful key design so task-thread drafts, plain thread drafts, and reply drafts stay separate.
  - Must degrade safely if `localStorage` is unavailable or blocked.

### Option B: Add server-backed draft saving endpoints and render drafts from the repository or a draft store
- Pros:
  - Drafts could survive browser changes and appear across devices.
  - Could support later features like explicit draft management or recovery after signing failures on another machine.
  - Moves persistence out of browser storage limits and browser privacy settings.
- Cons:
  - Much larger scope than the user story requires.
  - Introduces draft ownership, cleanup, and authentication questions that the current product does not solve.
  - Adds backend state for content that is intentionally not yet a canonical post record.

### Option C: Build a generic reusable draft framework for all compose-style pages first
- Pros:
  - Creates one pattern that could later cover thread, reply, task, and profile-update forms.
  - Reduces the chance of future duplication if more signed forms need draft persistence.
  - Encourages a consistent status/timestamp treatment across write surfaces.
- Cons:
  - Broader than necessary for the immediate thread-and-reply story.
  - Pulls profile-update and other forms into the loop before this narrower behavior is proven useful.
  - Risks turning a small reliability fix into a frontend architecture exercise.

## Recommendation
Recommend Option A: add local browser draft autosave to the existing shared compose page.

This is the best fit because the current compose flow is already centralized in shared HTML and shared browser-side signing logic, so the feature can stay narrow:

- persist only thread and reply body content plus any thread-specific fields already on the compose form,
- show a human-readable last-saved indicator directly on the compose page,
- scope storage keys to the compose context so different drafts do not collide,
- restore saved values on load before the user types again,
- clear the saved draft only after a successful submission,
- leave cross-device sync, named draft management, and server-side draft storage out of scope.

That solves the accidental reload/navigation problem directly with minimal moving parts, while keeping the door open to a later generalized draft system if more write surfaces prove they need it.
