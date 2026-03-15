## Problem
Thread and reply composition currently happens in the browser, but any accidental reload or navigation can wipe in-progress work before it is submitted. The next slice should add the smallest useful draft-preservation behavior so a user can recover local thread and reply drafts and see a visible last-saved timestamp without turning this into cross-device sync, backend draft storage, or a broader compose-system rewrite.

## User Stories
- As a browser user composing a new thread, I want my in-progress draft to survive accidental reloads or navigation so I do not lose what I wrote.
- As a browser user composing a reply, I want the draft to restore for the same reply target so I can continue where I left off.
- As a browser user, I want to see when the draft was last saved so I can tell whether my latest changes are already protected.
- As a future implementer, I want draft persistence to reuse the existing shared compose surface so thread, task-thread, and reply composition do not fork into separate implementations.

## Core Requirements
- The slice must preserve in-progress browser drafts for thread and reply compose flows using local browser storage.
- The slice must show a visible last-saved timestamp on the compose page when a draft has been stored.
- The slice must restore the saved draft automatically when the user returns to the same compose context.
- The slice must scope saved drafts so plain threads, task threads, and replies to different targets do not overwrite each other.
- The slice must clear the saved draft after a successful signed submission so stale text does not reappear unexpectedly.
- The slice must degrade safely when local browser storage is unavailable, without breaking compose or submission behavior.
- The slice must avoid server-side draft storage, cross-device synchronization, named draft management, or changes to the canonical post submission contract.

## Shared Component Inventory
- Existing web compose surface: reuse `templates/compose.html` as the one shared thread/reply compose template because draft status should appear in the existing signed compose UI rather than on a new page.
- Existing browser compose logic: extend `templates/assets/browser_signing.js` because it already owns shared thread/reply form behavior, local key storage, payload preview, and submit lifecycle.
- Existing compose routing: reuse the current `/compose/thread`, `/compose/task`, and `/compose/reply` routes because draft persistence should attach to the current compose contexts instead of adding new endpoints.
- Existing submission flow: keep `/api/create_thread` and `/api/create_reply` unchanged because draft persistence is a client-side resilience feature, not a new write contract.
- Existing task-thread fields: include the task-specific compose inputs in the same local draft model so typed root thread composition does not become a special case.

## Simple User Flow
1. A user opens a thread or reply compose page and starts typing.
2. The browser saves the current draft locally and updates the visible last-saved timestamp.
3. The user accidentally reloads the page or navigates away and later returns to the same compose context.
4. The compose form restores the saved draft automatically and continues showing the most recent saved time.
5. After a successful signed submission, the browser clears the saved draft for that compose context.

## Success Criteria
- A user can reload or accidentally leave `/compose/thread`, `/compose/task`, or `/compose/reply` and recover the prior local draft on return.
- The compose page shows a visible last-saved timestamp whenever a local draft exists.
- Different compose contexts keep separate drafts instead of overwriting one another.
- Successful signed submission clears the matching saved draft while preserving normal submit behavior.
- If browser storage is unavailable, compose and submission still work and the user receives a clear non-fatal status instead of a broken form.
