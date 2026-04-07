## Stage 1 - Shared timestamp display contract
- Changes:
  - Added a canonical timestamp display helper layer in `forum_web/web.py` for parsing ISO-style timestamps, generating friendly relative labels, generating exact UTC tooltip text, and rendering shared timestamp HTML.
  - Added focused tests covering UTC normalization, friendly relative labels for past and future times, and rendered tooltip/title output.
- Verification:
  - Ran `python -m pytest tests/test_site_activity_git_log_helpers.py`
  - Result: `21 passed`
- Notes:
  - This stage only introduced the shared contract and tests; no user-facing timestamp surfaces were switched over yet.

## Stage 2 - Home page thread timestamps
- Changes:
  - Extended the board index render path to load indexed root timestamps and render one `last active` timestamp per thread row using the shared friendly-plus-exact timestamp contract.
  - Added shared timestamp styling for tooltip-backed human-facing timestamp text.
  - Added board-index regression coverage for visible timestamp rendering and the no-index fallback case.
- Verification:
  - Ran `python -m pytest tests/test_board_index_page.py tests/test_site_activity_git_log_helpers.py`
  - Result: `35 passed`
- Notes:
  - The home page now shows thread recency only when indexed timestamps are available, preserving the previous lean fallback when index data is missing.
