## Stage 1 - Add shared compose requirements and ASCII rationale
- Changes:
  - Updated `templates/compose.html` so all compose surfaces now show a shared requirements-and-limitations block above the form.
  - Added concise ASCII rationale covering human-readable canonical text records, easier handling in ordinary text tools, and reduced Unicode-obfuscation risk.
  - Expanded compose coverage in `tests/test_compose_thread_page.py`, `tests/test_compose_reply_page.py`, and `tests/test_task_thread_pages.py` so thread, reply, and task compose pages all assert the new guidance.
- Verification:
  - Ran `python -m unittest tests.test_compose_thread_page tests.test_compose_reply_page tests.test_task_thread_pages`
- Notes:
  - This stage changes only the compose surfaces. The current instance-info framing remains in place until Stage 2.

## Stage 2 - Reframe `/instance/` as project information
- Changes:
  - Updated `forum_web/web.py` so `/instance/` now renders with project-information framing rather than narrow instance-info wording.
  - Expanded `templates/instance_info.html` with a project overview section and a compact FAQ-style panel while preserving the existing public facts and repository-derived metadata.
  - Expanded `tests/test_instance_info_page.py` so the carried-forward facts and the new explanatory content are both covered.
- Verification:
  - Ran `python -m unittest tests.test_instance_info_page tests.test_compose_thread_page tests.test_compose_reply_page tests.test_task_thread_pages`
- Notes:
  - The route remains `/instance/` in this stage. Only the page framing and content model changed.

## Stage 3 - Align navigation and regression coverage
- Changes:
  - Updated `forum_web/templates.py` so the shared primary nav now labels `/instance/` as `Project info`, aligning the renamed page framing with the rest of the site.
  - Expanded `tests/test_board_index_page.py` and `tests/test_instance_info_page.py` so the shared-nav label and the renamed project-information framing are both covered.
- Verification:
  - Ran `python -m unittest tests.test_board_index_page tests.test_instance_info_page tests.test_compose_thread_page tests.test_compose_reply_page tests.test_task_thread_pages`
- Notes:
  - The `/instance/` route remains intact in this stage; only the user-facing terminology changed.
