## Stage 1 - Add shared compose requirements and ASCII rationale
- Changes:
  - Updated `templates/compose.html` so all compose surfaces now show a shared requirements-and-limitations block above the form.
  - Added concise ASCII rationale covering human-readable canonical text records, easier handling in ordinary text tools, and reduced Unicode-obfuscation risk.
  - Expanded compose coverage in `tests/test_compose_thread_page.py`, `tests/test_compose_reply_page.py`, and `tests/test_task_thread_pages.py` so thread, reply, and task compose pages all assert the new guidance.
- Verification:
  - Ran `python -m unittest tests.test_compose_thread_page tests.test_compose_reply_page tests.test_task_thread_pages`
- Notes:
  - This stage changes only the compose surfaces. The current instance-info framing remains in place until Stage 2.
