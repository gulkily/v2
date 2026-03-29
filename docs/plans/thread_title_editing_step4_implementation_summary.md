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
