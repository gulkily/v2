## Stage 1 - action-area status surface
- Changes:
  - Moved the canonical `submit-status` element into the compose form's primary action area in [compose.html](/home/wsl/v2/templates/compose.html) so active submission feedback no longer reads like a footer note below the form.
  - Added a shared `compose-submit-area` and `compose-submit-status` styling contract in [site.css](/home/wsl/v2/templates/assets/site.css), including an explicit `data-status-tone` hook for idle versus active states.
  - Extended the thread and reply compose page tests in [test_compose_thread_page.py](/home/wsl/v2/tests/test_compose_thread_page.py) and [test_compose_reply_page.py](/home/wsl/v2/tests/test_compose_reply_page.py) to assert that the submit status now appears in the main action area with the idle tone contract.
- Verification:
  - Ran `python3 -m unittest tests.test_compose_thread_page tests.test_compose_reply_page`.
- Notes:
  - This stage changes structure and styling only. Browser status behavior still uses the existing text updates and will be wired into the new active-state hook in Stage 2.

## Stage 2 - active submit-status tone wiring
- Changes:
  - Extended the shared status helper in [browser_signing.js](/home/wsl/v2/templates/assets/browser_signing.js) with a small tone-aware path so status updates can set `data-status-tone` when needed.
  - Added `setSubmitStatus(...)` and `setActiveSubmitStatus(...)` helpers in [browser_signing.js](/home/wsl/v2/templates/assets/browser_signing.js) and switched the compose submission flow to use the active tone during payload building, PoW requirement checks, PoW solving, signing, unsigned fallback submission, and network submission.
  - Returned the action-area status to the idle tone for cleared-pending, success, and failure messages so the stronger treatment is reserved for work-in-progress states.
- Verification:
  - Ran `python3 -m unittest tests.test_browser_signing_normalization tests.test_compose_thread_page tests.test_compose_reply_page`.
- Notes:
  - This stage keeps the same user-facing copy and DOM ids; it only adds the state transition needed for the new visual emphasis contract.
