## Stage 1 - Shared timestamp display contract
- Changes:
  - Added a canonical timestamp display helper layer in `forum_web/web.py` for parsing ISO-style timestamps, generating friendly relative labels, generating exact UTC tooltip text, and rendering shared timestamp HTML.
  - Added focused tests covering UTC normalization, friendly relative labels for past and future times, and rendered tooltip/title output.
- Verification:
  - Ran `python -m pytest tests/test_site_activity_git_log_helpers.py`
  - Result: `21 passed`
- Notes:
  - This stage only introduced the shared contract and tests; no user-facing timestamp surfaces were switched over yet.
