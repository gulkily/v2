## Stage 1 - Extend commit activity metadata
- Changes:
  - Expanded `forum_web/web.py` so `GitCommitEntry` carries author metadata, short hashes, touched-file summaries, explicit `.md` highlights, canonical target identifiers, and an optional deterministic GitHub commit URL.
  - Added helper functions for commit-area classification, file-summary extraction, and GitHub commit URL derivation from the repository `origin` remote.
  - Expanded `tests/test_site_activity_git_log_helpers.py` to cover area classification, markdown detection, canonical target extraction, author metadata, and GitHub-link generation.
- Verification:
  - Ran `python -m unittest tests.test_site_activity_git_log_helpers`
- Notes:
  - This stage changes only the git activity model/helper layer. `/activity/` still renders the older compact commit cards until Stage 2 applies the richer metadata to the page.

## Stage 2 - Render richer commit cards on `/activity/`
- Changes:
  - Updated `forum_web/web.py` so commit cards render author metadata, short hashes, area summaries, touched-file lists, explicit markdown updates, canonical targets, and a GitHub link when derivable from the repository origin.
  - Expanded `tests/test_site_activity_page.py` with a mixed code-and-docs commit fixture and assertions covering the richer commit-card content inside the existing filtered activity timeline.
- Verification:
  - Ran `python -m unittest tests.test_site_activity_page tests.test_site_activity_git_log_helpers`
- Notes:
  - The card stays summary-oriented in this stage: it shows what changed and where to go next, but it still does not embed diffs or any full commit-browser behavior.

## Stage 3 - Align copy and coverage around outbound commit links
- Changes:
  - Updated `forum_web/web.py` so the activity-page intro copy explains that commit cards surface touched files and outbound GitHub links when available.
  - Expanded `tests/test_site_activity_git_log_helpers.py` with a non-GitHub remote regression to lock down the deterministic outbound-link behavior.
  - Expanded `tests/test_site_activity_page.py` so the richer page framing is covered alongside the existing commit-card assertions.
- Verification:
  - Ran `python -m unittest tests.test_board_index_page tests.test_site_activity_page tests.test_site_activity_git_log_helpers tests.test_instance_info_page tests.test_task_thread_pages`
- Notes:
  - This stage tightened the user-facing framing and remote-link assumptions without changing the route structure or turning `/activity/` into a remote-availability checker.
