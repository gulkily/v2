## Stage 1 - shared compose draft-status hooks
- Changes:
  - Added a visible `draft-status` line to the shared signed compose template so thread, task-thread, and reply pages all expose the same local-draft status area.
  - Added focused compose-page coverage for `/compose/thread`, `/compose/task`, and `/compose/reply` to lock in the shared draft-status hook.
- Verification:
  - Ran `python -m unittest tests.test_compose_thread_page tests.test_compose_reply_page tests.test_task_thread_pages`.
- Notes:
  - This stage only adds the shared UI hook and page coverage; browser-side autosave and restore behavior lands in Stage 2.

## Stage 2 - shared browser autosave and restore behavior
- Changes:
  - Extended `browser_signing.js` with compose-context draft keys, local-storage availability checks, saved-draft serialization, and restore-on-load behavior for thread, task-thread, and reply compose flows.
  - Added debounced local draft saving tied to the existing compose inputs so payload preview updates and local persistence stay in the same shared input lifecycle.
  - Added human-readable draft-status messages for initial state, restored drafts, fresh saves, and blocked local storage while leaving the profile-update flow outside the draft feature.
- Verification:
  - Ran `node --input-type=module --eval "import('node:fs/promises').then(async (fs) => { let source = await fs.readFile('templates/assets/browser_signing.js', 'utf8'); source = source.replace(/^import .*$/m, 'const openpgp = {};').replace(/main\\(\\);\\s*$/, ''); await import('data:text/javascript,' + encodeURIComponent(source)); console.log('browser_signing.js parsed'); });"` and confirmed the shared browser module still parses after the draft logic changes.
  - Ran `python -m unittest tests.test_compose_thread_page tests.test_compose_reply_page tests.test_task_thread_pages`.
- Notes:
  - Draft state remains browser-local by design; this stage does not change submission or clear-on-success behavior yet.
