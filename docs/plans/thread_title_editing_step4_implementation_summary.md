## Stage 1 - Record model and authority policy
- Changes:
  - Added the initial core thread-title update record and authority helpers.
  - Added focused Stage 1 unit coverage for parsing, flag behavior, and authorization policy.
- Verification:
  - `python -m unittest /home/wsl/v2/tests/test_thread_title_updates.py`
- Notes:
  - Stage 1 keeps the policy model independent of the submission path so later stages can reuse it cleanly.
