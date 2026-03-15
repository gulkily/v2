## Stage 1
- Goal: add the shared compose-page hooks for local draft status and define the compose-context boundary for stored drafts.
- Dependencies: approved Step 2; existing shared compose template and route rendering.
- Expected changes: extend the shared compose page with a visible draft-status element, expose any minimal data attributes needed to distinguish plain thread, task thread, and reply contexts, and keep the markup shared so thread and reply compose do not fork; planned helpers such as `composeDraftContext(root) -> { scopeKey: string, fieldNames: string[] }` and `renderComposePage(..., thread_type="", ...) -> str` continuing to drive one template.
- Verification approach: load `/compose/thread`, `/compose/task`, and `/compose/reply`, confirm the new draft-status UI renders on each page, and confirm the HTML exposes enough context to derive distinct local draft keys.
- Risks or open questions:
  - choosing a storage-key shape that separates reply targets cleanly without overfitting to current routes
  - keeping the status copy useful when no draft exists yet or when storage later proves unavailable
- Canonical components/API contracts touched: `templates/compose.html`; shared compose-page data attributes; visible compose status contract.

## Stage 2
- Goal: implement local autosave and restore behavior inside the shared browser compose module.
- Dependencies: Stage 1; existing `browser_signing.js` form-state and payload-preview logic.
- Expected changes: add local-storage read/write helpers, debounce or otherwise limit save frequency during typing, restore saved values into the compose form on load, update the visible last-saved timestamp, and include task-thread fields in the same saved draft model while leaving profile-update behavior unchanged; planned helpers such as `draftStorageAvailable() -> boolean`, `loadDraft(scopeKey) -> DraftState | null`, `saveDraft(scopeKey, draftState) -> void`, `applyDraft(form, draftState) -> void`, and `renderDraftStatus(meta) -> void`.
- Verification approach: run a browser-module parse smoke test, manually type on each compose surface, reload, and confirm the expected fields restore with the latest saved time shown; confirm different reply targets and thread types keep separate drafts.
- Risks or open questions:
  - restoring draft values without fighting existing defaults or preview generation order
  - handling malformed stored JSON or blocked storage without surfacing noisy errors to the user
- Canonical components/API contracts touched: `templates/assets/browser_signing.js`; browser-local draft payload shape; shared compose restore/save lifecycle.

## Stage 3
- Goal: clear saved drafts on successful submission and harden the feature with focused tests and graceful fallback behavior.
- Dependencies: Stage 2.
- Expected changes: remove the matching stored draft only after a successful signed thread or reply submission, leave drafts intact on validation or network failure, add page tests that assert the new draft-status hook is present on compose routes, add any minimal status-copy coverage needed for task compose, and retain a JS syntax smoke check for the shared browser module; planned helpers such as `clearDraft(scopeKey) -> void` and `handleSuccessfulSubmit(...) -> void`.
- Verification approach: run focused unittest modules for compose and task-thread pages, run the existing browser-module parse smoke check pattern against `browser_signing.js`, and manually confirm success clears the draft while failure preserves it.
- Risks or open questions:
  - avoiding accidental draft clearing during dry-run or failed-submit paths
  - keeping test coverage meaningful even though most draft behavior lives in browser-side code without a dedicated JS test harness
- Canonical components/API contracts touched: signed compose submit lifecycle; compose-page status/readback contract; focused compose page tests and browser-module smoke verification.
