## Stage 1 - shared compose draft-status hooks
- Changes:
  - Added a visible `draft-status` line to the shared signed compose template so thread, task-thread, and reply pages all expose the same local-draft status area.
  - Added focused compose-page coverage for `/compose/thread`, `/compose/task`, and `/compose/reply` to lock in the shared draft-status hook.
- Verification:
  - Ran `python -m unittest tests.test_compose_thread_page tests.test_compose_reply_page tests.test_task_thread_pages`.
- Notes:
  - This stage only adds the shared UI hook and page coverage; browser-side autosave and restore behavior lands in Stage 2.
