## Stage 1 - Extend commit activity metadata
- Changes:
  - Expanded `forum_web/web.py` so `GitCommitEntry` carries author metadata, short hashes, touched-file summaries, explicit `.md` highlights, canonical target identifiers, and an optional deterministic GitHub commit URL.
  - Added helper functions for commit-area classification, file-summary extraction, and GitHub commit URL derivation from the repository `origin` remote.
  - Expanded `tests/test_site_activity_git_log_helpers.py` to cover area classification, markdown detection, canonical target extraction, author metadata, and GitHub-link generation.
- Verification:
  - Ran `python -m unittest tests.test_site_activity_git_log_helpers`
- Notes:
  - This stage changes only the git activity model/helper layer. `/activity/` still renders the older compact commit cards until Stage 2 applies the richer metadata to the page.
