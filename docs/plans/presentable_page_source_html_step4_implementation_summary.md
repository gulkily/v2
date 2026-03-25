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

## Stage 3 - Bring direct-response and host-side HTML pages onto the same standard
- Changes:
  - Refactored the Python refresh-page and streamed-refresh HTML in [`forum_web/web.py`](/home/wsl/v2/forum_web/web.py) into readable multiline documents with a shared refresh-page style block, and reformatted the top-level fallback server-error page to stop emitting a single-line HTML body.
  - Added direct-response source assertions in [`tests/test_post_index_startup.py`](/home/wsl/v2/tests/test_post_index_startup.py) and [`tests/test_request_operation_events.py`](/home/wsl/v2/tests/test_request_operation_events.py), plus explicit host-page source assertions in [`tests/test_php_host_missing_config_page.py`](/home/wsl/v2/tests/test_php_host_missing_config_page.py) and [`tests/test_php_host_cache.py`](/home/wsl/v2/tests/test_php_host_cache.py).
- Verification:
  - `python -m unittest tests.test_post_index_startup.PostIndexStartupTests.test_board_request_shows_refresh_page_when_startup_index_is_stale tests.test_request_operation_events.RequestOperationEventsTests.test_request_failure_is_recorded_as_failed_operation tests.test_php_host_missing_config_page.PhpHostMissingConfigPageTests.test_missing_config_page_is_styled_and_actionable tests.test_php_host_cache.PhpHostCacheTests.test_php_host_shows_status_page_before_blocking_rebuild_request`
- Notes:
  - The PHP host page implementations were already structurally readable, so Stage 3 mainly locks that behavior in with regression coverage while bringing the remaining Python-only direct responses up to the same standard.
