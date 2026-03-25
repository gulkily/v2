## Stage 1 - Define the readable HTML output contract
- Changes:
  - Added shared HTML block helpers in [`forum_web/templates.py`](/home/wsl/v2/forum_web/templates.py) so the common page shell assembles multiline header, navigation, CTA, footer, and script blocks instead of collapsing them into single-line output.
  - Updated the shared compose-page test in [`tests/test_compose_thread_page.py`](/home/wsl/v2/tests/test_compose_thread_page.py) to assert the shell now emits multiline structural blocks in page source.
- Verification:
  - `python -m unittest tests.test_compose_thread_page.ComposeThreadPageTests.test_compose_thread_page_renders_shared_draft_status_hook tests.test_compose_thread_page.ComposeThreadPageTests.test_compose_thread_page_source_uses_multiline_shared_shell_blocks`
  - Manual render smoke check:
    `python - <<'PY' ... render_page(title='T', hero_kicker='K', hero_title='H', hero_text='X', content_html='<section>Body</section>') ... PY`
- Notes:
  - Stage 1 focuses on the shared shell contract only; route-specific direct HTML responses and PHP host pages remain for later stages.

## Stage 2 - Apply the contract to template-backed page responses
- Changes:
  - Added shared HTML block helpers in [`forum_web/web.py`](/home/wsl/v2/forum_web/web.py) and used them on reusable template-backed fragments such as post cards, board-index stats and rows, activity navigation, commit cards, compose references, thread reply sections, and body paragraph rendering.
  - Added focused source-formatting assertions in [`tests/test_board_index_page.py`](/home/wsl/v2/tests/test_board_index_page.py) and [`tests/test_task_thread_pages.py`](/home/wsl/v2/tests/test_task_thread_pages.py) so representative board and thread pages keep multiline structural output.
- Verification:
  - `python -m unittest tests.test_board_index_page.BoardIndexPageTests.test_board_index_uses_shared_page_shell tests.test_board_index_page.BoardIndexPageTests.test_board_index_source_uses_multiline_stats_and_thread_rows tests.test_task_thread_pages.TaskThreadPagesTests.test_task_thread_page_renders_structured_metadata tests.test_task_thread_pages.TaskThreadPagesTests.test_thread_page_source_uses_multiline_post_cards`
- Notes:
  - This stage stays inside template-backed routes only; refresh pages, top-level error HTML, and PHP host pages are still reserved for Stage 3.
