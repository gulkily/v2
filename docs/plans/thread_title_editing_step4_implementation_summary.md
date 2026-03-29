## Stage 1 - Record model and authority policy
- Changes:
  - Added the initial core thread-title update record and authority helpers.
  - Added focused Stage 1 unit coverage for parsing, flag behavior, and authorization policy.
- Verification:
  - `python -m unittest /home/wsl/v2/tests/test_thread_title_updates.py`
- Notes:
  - Stage 1 keeps the policy model independent of the submission path so later stages can reuse it cleanly.

## Stage 2 - Signed submission path
- Changes:
  - Added the canonical signed `update_thread_title` submission path in `forum_cgi`, including validation, signature verification, record storage, and plain-text result rendering.
  - Added `/api/update_thread_title` to the WSGI app and API discovery text surfaces.
  - Added request-level coverage for owner authorization, rejected non-owner writes, permissive-flag writes, and API discovery output.
- Verification:
  - `python -m unittest /home/wsl/v2/tests/test_thread_title_update_submission.py /home/wsl/v2/tests/test_llm_api.py /home/wsl/v2/tests/test_llms_txt.py`
- Notes:
  - This stage adds the canonical write path and API discovery updates without changing read surfaces yet.

## Stage 3 - Resolved title read surfaces
- Changes:
  - Added resolved current-title overlay support to board index, thread page, task/planning pages, text API thread/index reads, and PHP/native board snapshots.
  - Kept raw root-post subject data intact while exposing the resolved title at thread-level read surfaces.
  - Added focused visibility tests for HTML, API, task, and PHP/native read paths.
- Verification:
  - `python -m unittest tests.test_thread_title_update_visibility tests.test_task_thread_pages tests.test_php_native_reads tests.test_board_index_page.BoardIndexPageTests.test_board_index_uses_resolved_thread_title_when_update_record_exists`
- Notes:
  - This stage overlays current thread titles onto existing read surfaces without mutating root post content.

## Stage 4 - Browser title-change flow
- Changes:
  - Added a dedicated `/threads/<thread-id>/title` page that reuses the browser signing flow for thread-title updates.
  - Added a `change title` action on thread pages and a dedicated signed payload builder for `update_thread_title` in the shared browser asset.
  - Added page-level coverage for the new thread title update route and thread-page action link.
- Verification:
  - `python -m unittest tests.test_thread_title_update_page tests.test_thread_title_update_submission`
- Notes:
  - This stage reuses the existing browser signing flow instead of introducing a second client-side signing path.

## Stage 5 - Regression coverage and policy hardening
- Changes:
  - Added moderator authorization coverage for thread title updates.
  - Added an explicit regression that a successful title update leaves the stored root post `Subject:` unchanged while API read surfaces report the resolved current title.
  - Re-ran the focused end-to-end thread-title test set across parser, API, page, visibility, and discovery surfaces.
- Verification:
  - `python -m unittest tests.test_thread_title_updates tests.test_thread_title_update_submission tests.test_thread_title_update_visibility tests.test_thread_title_update_page tests.test_llm_api tests.test_llms_txt`
- Notes:
  - This stage closes the remaining policy and readback gaps without expanding the feature surface.
